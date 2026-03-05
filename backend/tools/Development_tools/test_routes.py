"""
HTTP Route Testing Script for Lerngruppentool API
Tests all routes via actual HTTP requests
"""
 
import requests
import json
import sys
import time
import hashlib
import os
import sqlite3
from datetime import datetime
 
 
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
 
 
class RoutesTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0
        self.test_data = {}
        self.run_id = int(time.time())
        self.auth_users = {
            'teacher': {
                'email': 'teacher1@gso.schule.koeln',
                'password_hash': 'hash'
            },
            'admin': {
                'email': 'admin1@gso.schule.koeln',
                'password_hash': 'hash'
            }
        }

    def _resolve_db_path(self):
        candidates = [
            os.path.join(os.getcwd(), 'data.db'),
            os.path.join(os.getcwd(), 'backend', 'data.db')
        ]

        for path in candidates:
            if os.path.exists(path):
                return path

        return candidates[0]

    def _mark_email_verified(self, email: str, test_name: str):
        """Mark a user's DOI as verified directly in DB for route-flow continuation tests."""
        try:
            db_path = self._resolve_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_email_verifications
                SET verified_at = datetime('now'), token_hash = NULL, expires_at = NULL
                WHERE user_id = (SELECT id FROM users WHERE email = ?)
            """, (email,))
            conn.commit()
            updated = cursor.rowcount
            conn.close()

            if updated > 0:
                self.passed += 1
                print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {test_name}")
                return True

            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}No verification row updated for {email}{Colors.RESET}")
            return False
        except Exception as e:
            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Error marking email verified: {str(e)}{Colors.RESET}")
            return False

    def test_api_error_request(self, method, endpoint, data=None, params=None, test_name="", auth_as=None, expected_error_contains=None):
        """Make HTTP request and verify API returns status='error'."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers(auth_as)

        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            json_data = response.json() if response.text else None

            if response.status_code >= 500:
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected API error response, got HTTP {response.status_code}{Colors.RESET}")
                print(f"  {Colors.RED}Response: {response.text[:200]}{Colors.RESET}")
                return None

            if not isinstance(json_data, dict) or json_data.get('status') != 'error':
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected API status='error', got: {response.text[:200]}{Colors.RESET}")
                return None

            if expected_error_contains and expected_error_contains.lower() not in (json_data.get('message', '').lower()):
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected error containing '{expected_error_contains}', got '{json_data.get('message')}'{Colors.RESET}")
                return None

            self.passed += 1
            print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {test_name}")
            print(f"  {Colors.CYAN}{method} {endpoint} → HTTP {response.status_code} (API error as expected){Colors.RESET}")
            return json_data

        except requests.exceptions.ConnectionError:
            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Cannot connect to {url}{Colors.RESET}")
            return None
        except Exception as e:
            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Error: {str(e)}{Colors.RESET}")
            return None
 
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
 
    def _get_auth_headers(self, auth_as: str = None):
        if not auth_as:
            return None
 
        user = self.auth_users.get(auth_as)
        if not user:
            print(f"{Colors.YELLOW}Auth user '{auth_as}' not found. Sending request without auth headers.{Colors.RESET}")
            return None
 
        return {
            'X-Auth-Email': user['email'],
            'X-Auth-Password-Hash': user['password_hash']
        }
   
    def test_request(self, method, endpoint, data=None, params=None, expected_status=200, test_name="", auth_as=None):
        """Make HTTP request and verify response"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers(auth_as)
       
        try:
            if method == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
           
            if response.status_code == expected_status:
                # Try to parse JSON response
                try:
                    json_data = response.json()
                except:
                    json_data = None
 
                if expected_status < 400 and isinstance(json_data, dict) and json_data.get('status') == 'error':
                    self.failed += 1
                    print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                    print(f"  {Colors.RED}HTTP {response.status_code}, aber API-Status ist error{Colors.RESET}")
                    print(f"  {Colors.RED}Response: {response.text[:200]}{Colors.RESET}")
                    return None
 
                self.passed += 1
                print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {test_name}")
                print(f"  {Colors.CYAN}{method} {endpoint} → {response.status_code}{Colors.RESET}")
                if isinstance(json_data, dict) and json_data.get('data'):
                    print(f"  {Colors.BLUE}Data: {json.dumps(json_data['data'], indent=2)[:100]}...{Colors.RESET}")
                return json_data
            else:
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected {expected_status}, got {response.status_code}{Colors.RESET}")
                print(f"  {Colors.RED}Response: {response.text[:200]}{Colors.RESET}")
                return None
               
        except requests.exceptions.ConnectionError:
            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Cannot connect to {url}{Colors.RESET}")
            print(f"  {Colors.YELLOW}Make sure the server is running: python backend/app.py{Colors.RESET}")
            return None
        except Exception as e:
            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Error: {str(e)}{Colors.RESET}")
            return None
   
    def test_server_health(self):
        """Test if server is running"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}========== SERVER HEALTH CHECK =========={Colors.RESET}")
        response = self.test_request('GET', '/', test_name="Server root endpoint")
        if response:
            print(f"  {Colors.GREEN}Server is running!{Colors.RESET}")
            return True
        return False
   
    def test_user_routes(self):
        """Test all user-related routes"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}========== USER ROUTES =========={Colors.RESET}")
 
        user1_email = f'testuser1_{self.run_id}@gso.schule.koeln'
        user2_email = f'testuser2_{self.run_id}@gso.schule.koeln'
        user1_password = 'password123'
        user2_password = 'password456'
       
        # Create user 1
        response = self.test_request('POST', '/api/users',
            data={'email': user1_email, 'password': user1_password},
            test_name="POST /api/users - Create user 1")
        if response and response.get('data'):
            self.test_data['user1_id'] = response['data']['id']
            self.auth_users['user1'] = {
                'email': user1_email,
                'password_hash': self._hash_password(user1_password)
            }
       
        # Create user 2
        response = self.test_request('POST', '/api/users',
            data={'email': user2_email, 'password': user2_password},
            test_name="POST /api/users - Create user 2")
        if response and response.get('data'):
            self.test_data['user2_id'] = response['data']['id']
            self.auth_users['user2'] = {
                'email': user2_email,
                'password_hash': self._hash_password(user2_password)
            }

        # Verify DOI endpoint exists and validates token
        self.test_api_error_request('GET', '/api/users/verify-email',
            params={'email': user1_email},
            test_name="GET /api/users/verify-email - Missing token returns API error",
            expected_error_contains='token')

        # Login before verification should fail
        self.test_api_error_request('POST', '/api/users/login',
            data={'email': user1_email, 'password': user1_password},
            test_name="POST /api/users/login - Unverified user blocked",
            expected_error_contains='verify')

        # Mark both users as verified for remaining route tests
        self._mark_email_verified(user1_email, "Mark user1 as verified in DB")
        self._mark_email_verified(user2_email, "Mark user2 as verified in DB")
       
        # Login user
        self.test_request('POST', '/api/users/login',
            data={'email': user1_email, 'password': user1_password},
            test_name="POST /api/users/login - Login user")
       
        # Get all users
        self.test_request('GET', '/api/users',
            params={'limit': 10, 'offset': 0},
            test_name="GET /api/users - Get all users",
            auth_as='teacher')
       
        # Get specific user
        if 'user1_id' in self.test_data:
            self.test_request('GET', f'/api/users/{self.test_data["user1_id"]}',
                test_name=f"GET /api/users/{self.test_data['user1_id']} - Get user by ID",
                auth_as='user1')
       
        # Update user
        if 'user1_id' in self.test_data:
            updated_user1_email = f'updated_{self.run_id}@gso.schule.koeln'
            self.test_request('PATCH', f'/api/users/{self.test_data["user1_id"]}',
                data={'email': updated_user1_email},
                test_name=f"PATCH /api/users/{self.test_data['user1_id']} - Update user",
                auth_as='user1')
            self.auth_users['user1']['email'] = updated_user1_email
   
    def test_group_routes(self):
        """Test all group-related routes"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}========== GROUP ROUTES =========={Colors.RESET}")
       
        if 'user1_id' not in self.test_data:
            print(f"{Colors.YELLOW}Skipping group tests - no user created{Colors.RESET}")
            return
       
        # Create group 1
        response = self.test_request('POST', '/api/groups',
            data={
                'organiser_id': self.test_data['user1_id'],
                'title': 'Test Study Group',
                'subject': 'Mathematics',
                'description': 'Learning math together',
                'max_users': 5
            },
            test_name="POST /api/groups - Create group 1",
            auth_as='user1')
        if response and response.get('data'):
            self.test_data['group1_id'] = response['data']['id']
       
        # Create group 2
        response = self.test_request('POST', '/api/groups',
            data={
                'organiser_id': self.test_data['user1_id'],
                'title': 'Physics Group'
            },
            test_name="POST /api/groups - Create group 2",
            auth_as='user1')
        if response and response.get('data'):
            self.test_data['group2_id'] = response['data']['id']
       
        # Get all groups
        self.test_request('GET', '/api/groups',
            params={'limit': 10, 'offset': 0},
            test_name="GET /api/groups - Get all groups",
            auth_as='user1')
       
        # Search groups
        self.test_request('GET', '/api/groups',
            params={'search': 'Math'},
            test_name="GET /api/groups?search=Math - Search groups",
            auth_as='user1')
       
        # Update group
        if 'group1_id' in self.test_data:
            self.test_request('PATCH', f'/api/groups/{self.test_data["group1_id"]}',
                data={'description': 'Updated description'},
                test_name=f"PATCH /api/groups/{self.test_data['group1_id']} - Update group",
                auth_as='user1')
       
        # Report group
        if 'group1_id' in self.test_data:
            self.test_request('POST', f'/api/groups/{self.test_data["group1_id"]}/report',
                data={},
                test_name=f"POST /api/groups/{self.test_data['group1_id']}/report - Report group",
                auth_as='user1')
       
        # Get user groups
        if 'user1_id' in self.test_data:
            self.test_request('GET', f'/api/users/{self.test_data["user1_id"]}/groups',
                test_name=f"GET /api/users/{self.test_data['user1_id']}/groups - Get user groups",
                auth_as='user1')
   
    def test_membership_routes(self):
        """Test group membership routes"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}========== MEMBERSHIP ROUTES =========={Colors.RESET}")
       
        if 'group1_id' not in self.test_data or 'user2_id' not in self.test_data:
            print(f"{Colors.YELLOW}Skipping membership tests - missing prerequisites{Colors.RESET}")
            return
       
        # Add member to group
        self.test_request('POST', f'/api/groups/{self.test_data["group1_id"]}/members',
            data={'user_id': self.test_data['user2_id']},
            test_name=f"POST /api/groups/{self.test_data['group1_id']}/members - Add member",
            auth_as='user1')

        # Get member count after adding one member
        self.test_request('GET', f'/api/groups/{self.test_data["group1_id"]}/members/count',
            test_name=f"GET /api/groups/{self.test_data['group1_id']}/members/count - Count members",
            auth_as='user1')

        # Get member count for non-existent group (expect API error)
        self.test_api_error_request('GET', '/api/groups/999999/members/count',
            test_name="GET /api/groups/999999/members/count - Non-existent group returns error",
            auth_as='user1',
            expected_error_contains='not found')

        # Remove member from group
        self.test_request('DELETE',
            f'/api/groups/{self.test_data["group1_id"]}/members/{self.test_data["user2_id"]}',
            expected_status=204,
            test_name=f"DELETE /api/groups/.../members/... - Remove member",
            auth_as='user1')

        # Get member count after removing the member
        self.test_request('GET', f'/api/groups/{self.test_data["group1_id"]}/members/count',
            test_name=f"GET /api/groups/{self.test_data['group1_id']}/members/count - Count after removal",
            auth_as='user1')
   
    def test_join_request_routes(self):
        """Test join request routes"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}========== JOIN REQUEST ROUTES =========={Colors.RESET}")
       
        if 'group1_id' not in self.test_data or 'user2_id' not in self.test_data:
            print(f"{Colors.YELLOW}Skipping join request tests - missing prerequisites{Colors.RESET}")
            return
       
        # Create join request
        response = self.test_request('POST', '/api/join-requests',
            data={
                'user_id': self.test_data['user2_id'],
                'group_id': self.test_data['group1_id'],
                'message': 'I want to join this group'
            },
            test_name="POST /api/join-requests - Create join request",
            auth_as='user2')
        if response and response.get('data'):
            self.test_data['request1_id'] = response['data']['id']
       
        # Get all join requests
        self.test_request('GET', '/api/join-requests',
            test_name="GET /api/join-requests - Get all requests",
            auth_as='user1')
       
        # Get join requests by group
        if 'group1_id' in self.test_data:
            self.test_request('GET', '/api/join-requests',
                params={'group_id': self.test_data['group1_id']},
                test_name=f"GET /api/join-requests?group_id=... - Filter by group",
                auth_as='user1')
       
        # Get specific join request
        if 'request1_id' in self.test_data:
            self.test_request('GET', f'/api/join-requests/{self.test_data["request1_id"]}',
                test_name=f"GET /api/join-requests/{self.test_data['request1_id']} - Get by ID",
                auth_as='user1')
       
        # Approve join request
        if 'request1_id' in self.test_data:
            self.test_request('POST', f'/api/join-requests/{self.test_data["request1_id"]}/approve',
                data={},
                test_name=f"POST /api/join-requests/{self.test_data['request1_id']}/approve - Approve request",
                auth_as='user1')
       
        # Create another request for rejection test
        response = self.test_request('POST', '/api/join-requests',
            data={
                'user_id': self.test_data['user2_id'],
                'group_id': self.test_data['group2_id']
            },
            test_name="POST /api/join-requests - Create request for rejection",
            auth_as='user2')
        if response and response.get('data'):
            request2_id = response['data']['id']
           
            # Reject join request
            self.test_request('POST', f'/api/join-requests/{request2_id}/reject',
                data={},
                test_name=f"POST /api/join-requests/{request2_id}/reject - Reject request",
                auth_as='user1')
   
    def test_filter_group_routes(self):
        """Test GET /api/groups/filter with various query parameters"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}========== FILTER GROUP ROUTES =========={Colors.RESET}")
 
        # Filter by subject
        self.test_request('GET', '/api/groups/filter',
            params={'subject': 'Mathematics'},
            test_name="GET /api/groups/filter?subject=Mathematics",
            auth_as='user1')
 
        # Filter by type
        self.test_request('GET', '/api/groups/filter',
            params={'type': 'online'},
            test_name="GET /api/groups/filter?type=online",
            auth_as='user1')
 
        # Filter by status
        self.test_request('GET', '/api/groups/filter',
            params={'status': 'active'},
            test_name="GET /api/groups/filter?status=active",
            auth_as='user1')
 
        # Filter by location
        self.test_request('GET', '/api/groups/filter',
            params={'location': 'Teams'},
            test_name="GET /api/groups/filter?location=Teams",
            auth_as='user1')
 
        # Filter by organiser_id
        if 'user1_id' in self.test_data:
            self.test_request('GET', '/api/groups/filter',
                params={'organiser_id': self.test_data['user1_id']},
                test_name=f"GET /api/groups/filter?organiser_id={self.test_data['user1_id']}",
                auth_as='user1')
 
        # Filter with has_space=true
        self.test_request('GET', '/api/groups/filter',
            params={'has_space': 'true'},
            test_name="GET /api/groups/filter?has_space=true",
            auth_as='user1')
 
        # Filter with has_space=false
        self.test_request('GET', '/api/groups/filter',
            params={'has_space': 'false'},
            test_name="GET /api/groups/filter?has_space=false",
            auth_as='user1')
 
        # Combined filter
        self.test_request('GET', '/api/groups/filter',
            params={'subject': 'Mathematics', 'type': 'online', 'status': 'active'},
            test_name="GET /api/groups/filter?subject+type+status combined",
            auth_as='user1')
 
        # Filter that returns no results
        self.test_request('GET', '/api/groups/filter',
            params={'subject': 'NonExistentSubject'},
            test_name="GET /api/groups/filter - no match returns empty list",
            auth_as='user1')
 
        # Pagination
        self.test_request('GET', '/api/groups/filter',
            params={'limit': 1, 'offset': 0},
            test_name="GET /api/groups/filter?limit=1&offset=0 - pagination",
            auth_as='user1')
 
    def test_delete_routes(self):
        """Test delete operations"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}========== DELETE ROUTES =========={Colors.RESET}")
       
        # Delete group
        if 'group2_id' in self.test_data:
            self.test_request('DELETE', f'/api/groups/{self.test_data["group2_id"]}',
                expected_status=204,
                test_name=f"DELETE /api/groups/{self.test_data['group2_id']} - Delete group",
                auth_as='user1')
   
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 50}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 50}{Colors.RESET}")
       
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
       
        print(f"\n{Colors.BOLD}Total Tests:{Colors.RESET} {total}")
        print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.RESET} {self.passed}")
        print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.RESET} {self.failed}")
        print(f"{Colors.BOLD}Pass Rate:{Colors.RESET} {pass_rate:.1f}%")
       
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 50}{Colors.RESET}\n")
       
        return self.failed == 0
   
    def run_all_tests(self):
        """Run all route tests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 50}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}LERNGRUPPENTOOL ROUTE TEST SUITE{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 50}{Colors.RESET}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base URL: {self.base_url}")
       
        if not self.test_server_health():
            print(f"\n{Colors.RED}{Colors.BOLD}Server is not running!{Colors.RESET}")
            print(f"{Colors.YELLOW}Please start the server first: python backend/app.py{Colors.RESET}")
            return 1
       
        self.test_user_routes()
        self.test_group_routes()
        self.test_filter_group_routes()
        self.test_membership_routes()
        self.test_join_request_routes()
        self.test_delete_routes()
       
        success = self.print_summary()
        return 0 if success else 1
 
 
if __name__ == '__main__':
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    tester = RoutesTester(base_url)
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
 
 