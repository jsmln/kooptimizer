from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

class CooperativeViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    @patch('apps.cooperatives.views.connection')
    def test_profile_form_view(self, mock_connection):
        # Mock DB responses for officer and profile
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        # Officer found
        mock_cursor.fetchone.side_effect = [ (1,), (None,), None ]
        mock_cursor.description = [type('col', (), {'name': 'coop_id'})]
        response = self.client.get(reverse('profile_form'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('cooperatives/profile_form.html', [t.name for t in response.templates])

    @patch('apps.cooperatives.views.connection')
    def test_create_profile(self, mock_connection):
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.side_effect = [ (1,), None ]
        # Simulate file upload
        coc_file = SimpleUploadedFile('coc.pdf', b'dummydata')
        cte_file = SimpleUploadedFile('cte.pdf', b'dummydata')
        data = {
            'coop_address': '123 Main St',
            'coop_contact': '1234567890',
            'coop_email': 'test@coop.com',
            'cda_reg_num': 'REG123',
            'cda_reg_date': '2020-01-01',
            'lccdc_membership': 'yes',
            'lccdc_membership_date': '2020-02-01',
            'area_operation': 'Area 1',
            'business_activity': 'Farming',
            'num_bod': '5',
            'num_se': '2',
            'coc': 'yes',
            'cte': 'yes',
            'assets_value': '1000',
            'paid_up_capital_value': '500',
            'net_surplus_value': '200',
            'reporting_year': '2025',
            'member_name[]': ['Alice'],
            'member_gender[]': ['F'],
            'member_mobile[]': ['123'],
            'member_email[]': ['alice@email.com'],
        }
        files = {
            'coc_file': coc_file,
            'cte_file': cte_file,
        }
        response = self.client.post(reverse('create_profile'), data, files=files)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': True, 'message': 'Profile saved successfully'})

    @patch('apps.cooperatives.views.connection')
    def test_download_attachment_invalid_type(self, mock_connection):
        response = self.client.get(reverse('download_attachment', args=[1, 'invalid']))
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid attachment type', response.content)

    @patch('apps.cooperatives.views.connection')
    def test_download_attachment_file_not_found(self, mock_connection):
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = None
        response = self.client.get(reverse('download_attachment', args=[1, 'coc']))
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'File not found', response.content)
