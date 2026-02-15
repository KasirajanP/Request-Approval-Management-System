import json
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from .models import Request

User = get_user_model()


class RequestApprovalAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.employee = User.objects.create_user(
            username='employee1',
            password='StrongPass123!',
            role=User.ROLE_EMPLOYEE,
        )
        self.approver = User.objects.create_user(
            username='approver1',
            password='StrongPass123!',
            role=User.ROLE_APPROVER,
        )
        self.other_approver = User.objects.create_user(
            username='approver2',
            password='StrongPass123!',
            role=User.ROLE_APPROVER,
        )

    def authenticate(self, username: str, password: str) -> None:
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps({'username': username, 'password': password}),
            content_type='application/json',
        )
        access = response.json()['access']
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {access}'

    def test_register_user(self):
        payload = {
            'username': 'employee2',
            'password': 'StrongPass123!',
            'role': User.ROLE_EMPLOYEE,
        }
        response = self.client.post(
            '/api/auth/register',
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertTrue(User.objects.filter(username='employee2').exists())

    def test_login_returns_jwt_tokens(self):
        payload = {'username': 'employee1', 'password': 'StrongPass123!'}
        response = self.client.post(
            '/api/auth/login',
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_employee_can_create_request(self):
        self.authenticate('employee1', 'StrongPass123!')
        payload = {
            'title': 'Laptop Request',
            'description': 'Need a laptop for development.',
            'assigned_approver': self.approver.id,
        }
        response = self.client.post(
            '/api/requests/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        request_obj = Request.objects.get(id=response.data['id'])
        self.assertEqual(request_obj.status, Request.STATUS_PENDING)
        self.assertEqual(request_obj.created_by_id, self.employee.id)

    def test_approver_cannot_create_request(self):
        self.authenticate('approver1', 'StrongPass123!')
        payload = {
            'title': 'Invalid Request',
            'description': 'Approver should not create this.',
            'assigned_approver': self.other_approver.id,
        }
        response = self.client.post(
            '/api/requests/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_employee_sees_only_their_requests(self):
        other_employee = User.objects.create_user(
            username='employee2',
            password='StrongPass123!',
            role=User.ROLE_EMPLOYEE,
        )
        own_request = Request.objects.create(
            title='Own request',
            description='Visible to owner',
            created_by=self.employee,
            assigned_approver=self.approver,
        )
        Request.objects.create(
            title='Other request',
            description='Should not be visible',
            created_by=other_employee,
            assigned_approver=self.approver,
        )

        self.authenticate('employee1', 'StrongPass123!')
        response = self.client.get('/api/requests/my/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], own_request.id)

    def test_assigned_approver_can_approve_once(self):
        request_obj = Request.objects.create(
            title='Approval test',
            description='Awaiting decision',
            created_by=self.employee,
            assigned_approver=self.approver,
        )
        self.authenticate('approver1', 'StrongPass123!')

        first_action = self.client.post(
            f'/api/requests/{request_obj.id}/action/',
            data=json.dumps({'action': 'APPROVE'}),
            content_type='application/json',
        )
        self.assertEqual(first_action.status_code, HTTPStatus.OK)
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, Request.STATUS_APPROVED)

        second_action = self.client.post(
            f'/api/requests/{request_obj.id}/action/',
            data=json.dumps({'action': 'REJECT'}),
            content_type='application/json',
        )
        self.assertEqual(second_action.status_code, HTTPStatus.BAD_REQUEST)

    def test_only_assigned_approver_can_act(self):
        request_obj = Request.objects.create(
            title='Assignment enforcement',
            description='Only assigned approver can decide',
            created_by=self.employee,
            assigned_approver=self.approver,
        )
        self.authenticate('approver2', 'StrongPass123!')
        response = self.client.post(
            f'/api/requests/{request_obj.id}/action/',
            data=json.dumps({'action': 'APPROVE'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
