import logging

from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from project.models import Project


User = get_user_model()


class ProjectsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logger = logging.getLogger('project.views')
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.ERROR)  # Ensure ERROR level logs are captured

        self.user = User.objects.create_user(
            name='testuser',
            email='testuser@gmail.com',
            password='testpass123'
        )

        self.project1 = Project.objects.create(
            name='Project 1',
            created_by=self.user
        )

        self.project2 = Project.objects.create(
            name='Project 2',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)

    def test_projects_view_authenticated_user(self):
        """Test normal case: authenticated user with projects"""
        self.client.login(email='testuser@gmail.com', password='testpass123')
        response = self.client.get(reverse('project:projects'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/projects.html')

        projects_list = response.context['projects']

        self.assertEqual(len(projects_list), 2)
        # Check sorting (newest first)
        self.assertEqual(projects_list[0].name, 'Project 2')
        self.assertEqual(projects_list[1].name, 'Project 1')

    def test_projects_view_no_projects(self):
        """Test edge case: authenticated user with no projects"""
        Project.objects.all().delete()  # Clear projects
        
        self.client.login(email='testuser@gmail.com', password='testpass123')
        response = self.client.get(reverse('project:projects'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/projects.html')
        
        projects_list = response.context['projects']
        
        self.assertEqual(len(projects_list), 0)

    def test_projects_view_unauthenticated_user(self):
        """Test invalid input: unauthenticated user"""
        response = self.client.get(reverse('project:projects'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    @patch('project.models.Project.objects.select_related')
    def test_projects_view_database_error(self, mock_select_related):
        """Test edge case: database query fails"""
        mock_query = mock_select_related.return_value
        mock_query.filter.side_effect = Exception("Database error")

        self.client.login(email='testuser@gmail.com', password='testpass123')

        with self.assertLogs('project.views', level='ERROR') as cm:
            response = self.client.get(reverse('project:projects'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/projects.html')
        
        projects_list = response.context['projects']

        self.assertEqual(len(projects_list), 0)
        self.assertIn('Error fetching projects: Database error', cm.output[0])

        messages = list(response.wsgi_request._messages)

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'An error occurred while fetching projects.')

    def test_projects_view_ordering(self):
        """Test normal case: verify projects are sorted by created_at descending"""
        self.client.login(email='testuser@gmail.com', password='testpass123')
        response = self.client.get(reverse('project:projects'))

        projects_list = response.context['projects']

        self.assertTrue(all(projects_list[i].created_at >= projects_list[i+1].created_at 
                        for i in range(len(projects_list)-1)))

    def test_projects_view_created_by_filter(self):
        """Test normal case: only user's projects are returned"""
        other_user = User.objects.create_user(
            name='otheruser',
            email='otheruser@gmail.com',
            password='testpass123'
        )
        Project.objects.create(
            name='Other User Project',
            created_by=other_user
        )

        self.client.login(email='testuser@gmail.com', password='testpass123')
        response = self.client.get(reverse('project:projects'))

        projects_list = response.context['projects']
        
        self.assertEqual(len(projects_list), 2)
        self.assertTrue(all(project.created_by == self.user for project in projects_list))
        

