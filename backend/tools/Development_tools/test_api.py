"""
Comprehensive API Testing Script for Lerngruppentool
Tests all modules, functions, and database integrity.
"""
 
import sqlite3
import sys
import os
import urllib.parse
from datetime import datetime
 
# Add project root and backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
 
from tools.dbConnector import DBConnector
from tools.Development_tools.dbCreator import Database
from modules.user.create_user import create_user, verify_user_email
from modules.user.get_user import get_user, get_all_users
from modules.user.update_user import update_user
from modules.user.delete_user import delete_user
from modules.user.login_user import login_user
from modules.user.get_user_groups import get_user_groups
from modules.group.create_group import create_group
from modules.group.get_all_groups import get_all_groups
from modules.group.filter_groups import filter_groups
from modules.group.update_group import update_group
from modules.group.delete_group import delete_group
from modules.group.report_group import report_group
from modules.group_membership.add_member import add_group_member
from modules.group_membership.remove_member import remove_group_member
from modules.join_group_request.create_join_request import create_beitrittsanfrage
from modules.join_group_request.get_join_request import get_join_requests, get_join_request_by_id
from modules.join_group_request.delete_join_request import delete_beitrittsanfrage
from modules.join_group_request.approve_join_request import approve_join_request, reject_join_request
from tools.logger import log
 
 

from tools.dbConnector import DBConnector
from tools.Development_tools.dbCreator import Database
from modules.user.create_user import create_user, verify_user_email
import modules.user.create_user as create_user_module
from modules.user.get_user import get_user, get_all_users
from modules.user.update_user import update_user
from modules.user.delete_user import delete_user
from modules.user.login_user import login_user
from modules.user.get_user_groups import get_user_groups
from modules.group.create_group import create_group
from modules.group.get_all_groups import get_all_groups
from modules.group.update_group import update_group
from modules.group.delete_group import delete_group
from modules.group.report_group import report_group
from modules.group_membership.add_member import add_group_member
from modules.group_membership.remove_member import remove_group_member
from modules.join_group_request.create_join_request import create_beitrittsanfrage
import modules.join_group_request.create_join_request as create_join_request_module
import modules.join_group_request.approve_join_request as approve_join_request_module
import modules.join_group_request.delete_join_request as delete_join_request_module
from modules.join_group_request.get_join_request import get_join_requests, get_join_request_by_id
from modules.join_group_request.delete_join_request import delete_beitrittsanfrage
from modules.join_group_request.approve_join_request import approve_join_request, reject_join_request


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
 
 
class APITester:
    def __init__(self, db_path="test_data.db"):
        self.db_path = db_path
        self.db = None
        self.db_connector = None
        self.test_results = []
        self.passed = 0
        self.failed = 0
       
        self.sent_emails = []
        self.sent_template_emails = []
        self._original_send_email = None
        self._original_send_template_email = None
        self._send_email_existed = False

    def _mock_send_email(self, **kwargs):
        """Capture outbound notification emails without sending them."""
        self.sent_emails.append(kwargs)
        return True

    def _mock_send_template_email(self, email_address, template_type, placeholders=None):
        """Capture outbound template emails (double opt-in) without sending them."""
        self.sent_template_emails.append({
            'email_address': email_address,
            'template_type': template_type,
            'placeholders': placeholders or {}
        })
        return True

    def _get_verification_payload_for_email(self, email):
        """Extract verification token+email from the latest DOI mail for a recipient."""
        for mail in reversed(self.sent_template_emails):
            if mail.get('email_address') != email:
                continue

            confirmation_link = (mail.get('placeholders') or {}).get('confirmation_link', '')
            parsed = urllib.parse.urlparse(confirmation_link)
            query = urllib.parse.parse_qs(parsed.query)
            token = query.get('token', [None])[0]
            link_email = query.get('email', [None])[0]
            if token and link_email:
                return token, link_email

        return None, None
        
    def setup(self):
        """Initialize test database"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}========== SETUP =========={Colors.RESET}")
       
        # Remove old test database if exists
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            print(f"{Colors.YELLOW}Removed old test database{Colors.RESET}")
       
        # Create new database
        self.db = Database(self.db_path)
        self.db.init_db()
        print(f"{Colors.GREEN}✓ Database schema created{Colors.RESET}")
       
        # Create connector
        self.db_connector = DBConnector(self.db_path)
        print(f"{Colors.GREEN}✓ Database connector initialized{Colors.RESET}")
   

        # Mock email sending for join request notifications
        self.sent_emails = []
        self.sent_template_emails = []
        self._send_email_existed = hasattr(create_join_request_module.email_sender, 'send_email')
        self._original_send_email = getattr(create_join_request_module.email_sender, 'send_email', None)
        self._original_send_template_email = getattr(create_user_module, 'send_template_email', None)
        create_join_request_module.email_sender.send_email = self._mock_send_email
        approve_join_request_module.email_sender.send_email = self._mock_send_email
        delete_join_request_module.email_sender.send_email = self._mock_send_email
        create_user_module.send_template_email = self._mock_send_template_email
        print(f"{Colors.GREEN}✓ Email sender mocked for tests{Colors.RESET}")
    
    def teardown(self):
        """Clean up after tests"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}========== TEARDOWN =========={Colors.RESET}")

        # Restore original email sender
        if self._send_email_existed:
            create_join_request_module.email_sender.send_email = self._original_send_email
            approve_join_request_module.email_sender.send_email = self._original_send_email
            delete_join_request_module.email_sender.send_email = self._original_send_email
        else:
            if hasattr(create_join_request_module.email_sender, 'send_email'):
                delattr(create_join_request_module.email_sender, 'send_email')

        create_user_module.send_template_email = self._original_send_template_email

        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            print(f"{Colors.GREEN}✓ Test database removed{Colors.RESET}")
   
    def assert_success(self, result, test_name):
        """Assert that result status is 'success'"""
        if result and result.get('status') == 'success':
            self.passed += 1
            print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {test_name}")
            self.test_results.append((test_name, True, None))
            return True
        else:
            self.failed += 1
            error = result.get('message', 'Unknown error') if result else 'No result'
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Error: {error}{Colors.RESET}")
            self.test_results.append((test_name, False, error))
            return False
   
    def assert_error(self, result, test_name, expected_error=None):
        """Assert that result status is 'error'"""
        if result and result.get('status') == 'error':
            if expected_error and expected_error.lower() not in result.get('message', '').lower():
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected error containing '{expected_error}', got: {result.get('message')}{Colors.RESET}")
                self.test_results.append((test_name, False, f"Wrong error message"))
                return False
            self.passed += 1
            print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {test_name} (correctly returned error)")
            self.test_results.append((test_name, True, None))
            return True
        else:
            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Expected error but got: {result}{Colors.RESET}")
            self.test_results.append((test_name, False, "Expected error"))
            return False
   
    def verify_db_count(self, table, expected_count, test_name):
        """Verify record count in database table"""
        conn = self.db_connector.connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        actual_count = cursor.fetchone()[0]
        conn.close()
       
        if actual_count == expected_count:
            self.passed += 1
            print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {test_name} (count: {actual_count})")
            self.test_results.append((test_name, True, None))
            return True
        else:
            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Expected {expected_count} records, got {actual_count}{Colors.RESET}")
            self.test_results.append((test_name, False, f"Count mismatch: {actual_count} != {expected_count}"))
            return False
   

    def verify_email_sent(self, expected_count, test_name, recipient=None, template_name=None, subject=None, body_contains=None):
        """Verify captured notification email count and optional payload fields."""
        actual_count = len(self.sent_emails)

        if actual_count != expected_count:
            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Expected {expected_count} sent emails, got {actual_count}{Colors.RESET}")
            self.test_results.append((test_name, False, f"Email count mismatch: {actual_count} != {expected_count}"))
            return False

        if expected_count > 0:
            last_email = self.sent_emails[-1]
            if recipient and last_email.get('to') != recipient:
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected recipient '{recipient}', got '{last_email.get('to')}'{Colors.RESET}")
                self.test_results.append((test_name, False, "Wrong email recipient"))
                return False

            if template_name and last_email.get('template_name') != template_name:
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected template '{template_name}', got '{last_email.get('template_name')}'{Colors.RESET}")
                self.test_results.append((test_name, False, "Wrong email template"))
                return False

            if subject and last_email.get('subject') != subject:
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected subject '{subject}', got '{last_email.get('subject')}'{Colors.RESET}")
                self.test_results.append((test_name, False, "Wrong email subject"))
                return False

            if body_contains and body_contains not in (last_email.get('body') or ''):
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected body to contain '{body_contains}', got '{last_email.get('body')}'{Colors.RESET}")
                self.test_results.append((test_name, False, "Wrong email body"))
                return False

        self.passed += 1
        print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {test_name} (emails: {actual_count})")
        self.test_results.append((test_name, True, None))
        return True

    def verify_template_email_sent(self, expected_count, test_name, recipient=None, template_type=None, link_contains=None):
        """Verify captured template email count and optional payload fields."""
        actual_count = len(self.sent_template_emails)

        if actual_count != expected_count:
            self.failed += 1
            print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
            print(f"  {Colors.RED}Expected {expected_count} template emails, got {actual_count}{Colors.RESET}")
            self.test_results.append((test_name, False, f"Template email count mismatch: {actual_count} != {expected_count}"))
            return False

        if expected_count > 0:
            last_email = self.sent_template_emails[-1]

            if recipient and last_email.get('email_address') != recipient:
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected recipient '{recipient}', got '{last_email.get('email_address')}'{Colors.RESET}")
                self.test_results.append((test_name, False, "Wrong template email recipient"))
                return False

            if template_type and last_email.get('template_type') != template_type:
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected template type '{template_type}', got '{last_email.get('template_type')}'{Colors.RESET}")
                self.test_results.append((test_name, False, "Wrong template email type"))
                return False

            confirmation_link = (last_email.get('placeholders') or {}).get('confirmation_link', '')
            if link_contains and link_contains not in confirmation_link:
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} {test_name}")
                print(f"  {Colors.RED}Expected confirmation link containing '{link_contains}', got '{confirmation_link}'{Colors.RESET}")
                self.test_results.append((test_name, False, "Wrong confirmation link"))
                return False

        self.passed += 1
        print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} {test_name} (template emails: {actual_count})")
        self.test_results.append((test_name, True, None))
        return True
    
    def test_user_operations(self):
        """Test all user-related operations"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}========== USER OPERATIONS =========={Colors.RESET}")
       
        # Test 1: Create user with valid data
        result = create_user(self.db_connector, {
            'email': 'test1@gso.schule.koeln',
            'password': 'password123'
        })
        self.assert_success(result, "Create user with valid data")
        if result.get('status') == 'success':
            self.verify_template_email_sent(
                1,
                "Send DOI mail on first user creation",
                recipient='test1@gso.schule.koeln',
                template_type='double_opt_in',
                link_contains='/api/users/verify-email'
            )
        user1_id = result['data']['id'] if result.get('status') == 'success' else None
       
        # Test 2: Create another user
        result = create_user(self.db_connector, {
            'email': 'test2@gso.schule.koeln',
            'password': 'password456'
        })
        self.assert_success(result, "Create second user")
        if result.get('status') == 'success':
            self.verify_template_email_sent(
                2,
                "Send DOI mail on second user creation",
                recipient='test2@gso.schule.koeln',
                template_type='double_opt_in',
                link_contains='/api/users/verify-email'
            )
        user2_id = result['data']['id'] if result.get('status') == 'success' else None
       
        # Test 3: Create user with duplicate email
        result = create_user(self.db_connector, {
            'email': 'test1@gso.schule.koeln',
            'password': 'password789'
        })
        self.assert_error(result, "Create user with duplicate email", "already exists")
       
        # Test 4: Create user with missing email
        result = create_user(self.db_connector, {
            'password': 'password123'
        })
        self.assert_error(result, "Create user with missing email", "required")
       
        # Test 5: Create user with invalid email
        result = create_user(self.db_connector, {
            'email': 'invalid-email',
            'password': 'password123'
        })
        self.assert_error(result, "Create user with invalid email", "gso")
       
        # Test 5a: Create user with bad word in email
        result = create_user(self.db_connector, {
            'email': 'fuck@gso.schule.koeln',
            'password': 'password123'
        })
        self.assert_error(result, "Create user with bad word in email", "inappropriate")
       
        # Test 5b: Create user with German bad word in email
        result = create_user(self.db_connector, {
            'email': 'scheiße@gso.schule.koeln',
            'password': 'password123'
        })
        self.assert_error(result, "Create user with German bad word in email", "inappropriate")
       
        # Test 6: Get user by ID
        if user1_id:
            result = get_user(self.db_connector, user1_id)
            self.assert_success(result, "Get user by ID")
       
        # Test 7: Get non-existent user
        result = get_user(self.db_connector, 99999)
        self.assert_error(result, "Get non-existent user", "not found")
       
        # Test 8: Get all users
        result = get_all_users(self.db_connector, limit=10, offset=0)
        self.assert_success(result, "Get all users")
        if result.get('status') == 'success':
            users_count = result['data']['total']
            if users_count == 2:
                print(f"{Colors.GREEN}  ✓ Correct user count: {users_count}{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 2 users, got {users_count}{Colors.RESET}")
       
        # Test 9: Login before email verification should fail
        result = login_user(self.db_connector, {
            'email': 'test1@gso.schule.koeln',
            'password': 'password123'
        })
        self.assert_error(result, "Login before DOI verification", "verify")

        # Test 9a: Verify user1 via DOI token
        token, token_email = self._get_verification_payload_for_email('test1@gso.schule.koeln')
        if token and token_email:
            result = verify_user_email(self.db_connector, token, token_email)
            self.assert_success(result, "Verify user1 email via DOI token")

            # Verify idempotent behavior for already verified token/email pair
            result = verify_user_email(self.db_connector, token, token_email)
            self.assert_error(result, "Verify user1 again with consumed token", "invalid")

        # Test 9b: Login after verification should work
        result = login_user(self.db_connector, {
            'email': 'test1@gso.schule.koeln',
            'password': 'password123'
        })
        self.assert_success(result, "Login with verified credentials")
       
        # Test 10: Login with incorrect password
        result = login_user(self.db_connector, {
            'email': 'test1@gso.schule.koeln',
            'password': 'wrongpassword'
        })
        self.assert_error(result, "Login with incorrect password", "invalid")
       
        # Test 11: Update user email
        if user1_id:
            result = update_user(self.db_connector, user1_id, {
                'email': 'updated@gso.schule.koeln'
            })
            self.assert_success(result, "Update user email")
       
        # Test 12: Update user password
        if user1_id:
            result = update_user(self.db_connector, user1_id, {
                'password': 'newpassword123'
            })
            self.assert_success(result, "Update user password")
           
            # Verify new password works
            result = login_user(self.db_connector, {
                'email': 'updated@gso.schule.koeln',
                'password': 'newpassword123'
            })
            self.assert_success(result, "Login with updated password")
       
        # Test 13: Update user with duplicate email
        if user1_id and user2_id:
            result = update_user(self.db_connector, user1_id, {
                'email': 'test2@gso.schule.koeln'
            })
            self.assert_error(result, "Update user with duplicate email", "already exists")
       
        # Test 13a: Update user with bad word in email
        if user1_id:
            result = update_user(self.db_connector, user1_id, {
                'email': 'bitch@gso.schule.koeln'
            })
            self.assert_error(result, "Update user with bad word in email", "inappropriate")
       
        # Test 14: Verify database count
        self.verify_db_count('users', 2, "Verify users table count")
       
        return user1_id, user2_id
   
    def test_group_operations(self, user1_id, user2_id):
        """Test all group-related operations"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}========== GROUP OPERATIONS =========={Colors.RESET}")
       
        # Test 1: Create group with valid data
        result = create_group(self.db_connector, {
            'organiser_id': user1_id,
            'title': 'Test Study Group',
            'subject': 'Mathematics',
            'topic': 'Calculus',
            'description': 'Learning calculus together',
            'class': 'FI302',
            'type': 'online',
            'location': 'Teams',
            'max_users': 5
        })
        self.assert_success(result, "Create group with valid data")
        group1_id = result['data']['id'] if result.get('status') == 'success' else None
       
        # Test 2: Create group with minimal data
        result = create_group(self.db_connector, {
            'organiser_id': user2_id,
            'title': 'Physics Group'
        })
        self.assert_success(result, "Create group with minimal data")
        group2_id = result['data']['id'] if result.get('status') == 'success' else None
       
        # Test 3: Create group without organiser_id
        result = create_group(self.db_connector, {
            'title': 'Invalid Group'
        })
        self.assert_error(result, "Create group without organiser_id", "required")
       
        # Test 4: Create group with non-existent organiser
        result = create_group(self.db_connector, {
            'organiser_id': 99999,
            'title': 'Invalid Group'
        })
        self.assert_error(result, "Create group with non-existent organiser", "not found")
       
        # Test 4a: Create group with bad word in title
        result = create_group(self.db_connector, {
            'organiser_id': user1_id,
            'title': 'This is shit group'
        })
        self.assert_error(result, "Create group with bad word in title", "inappropriate")
       
        # Test 4b: Create group with bad word in description
        result = create_group(self.db_connector, {
            'organiser_id': user1_id,
            'title': 'Clean Title',
            'description': 'This fucking sucks'
        })
        self.assert_error(result, "Create group with bad word in description", "inappropriate")
       
        # Test 4c: Create group with German bad word in topic
        result = create_group(self.db_connector, {
            'organiser_id': user1_id,
            'title': 'Clean Title',
            'topic': 'arschloch topic'
        })
        self.assert_error(result, "Create group with German bad word in topic", "inappropriate")
       
        # Test 4d: Create group with bad word in location
        result = create_group(self.db_connector, {
            'organiser_id': user1_id,
            'title': 'Clean Title',
            'location': 'damn place'
        })
        self.assert_error(result, "Create group with bad word in location", "inappropriate")
       
        # Test 5: Get all groups
        result = get_all_groups(self.db_connector, limit=10, offset=0)
        self.assert_success(result, "Get all groups")
        if result.get('status') == 'success':
            groups_count = result['data']['total']
            if groups_count == 2:
                print(f"{Colors.GREEN}  ✓ Correct group count: {groups_count}{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 2 groups, got {groups_count}{Colors.RESET}")
       
        # Test 6: Search groups
        result = get_all_groups(self.db_connector, limit=10, offset=0, search='Math')
        self.assert_success(result, "Search groups by keyword")
        if result.get('status') == 'success':
            found = result['data']['total']
            if found == 1:
                print(f"{Colors.GREEN}  ✓ Search found correct number: {found}{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 1 group in search, got {found}{Colors.RESET}")
       
        # Test 7: Update group
        if group1_id:
            result = update_group(self.db_connector, group1_id, {
                'title': 'Updated Study Group',
                'description': 'Updated description',
                'max_users': 10
            })
            self.assert_success(result, "Update group data")
       
        # Test 8: Update group with invalid max_users
        if group1_id:
            result = update_group(self.db_connector, group1_id, {
                'max_users': -5
            })
            self.assert_error(result, "Update group with negative max_users", "must be")
       
        # Test 8a: Update group with bad word in title
        if group1_id:
            result = update_group(self.db_connector, group1_id, {
                'title': 'Stupid group title'
            })
            self.assert_error(result, "Update group with bad word in title", "inappropriate")
       
        # Test 8b: Update group with bad word in description
        if group1_id:
            result = update_group(self.db_connector, group1_id, {
                'description': 'This is a damn bad description'
            })
            self.assert_error(result, "Update group with bad word in description", "inappropriate")
       
        # Test 8c: Update group with German bad word in subject
        if group1_id:
            result = update_group(self.db_connector, group1_id, {
                'subject': 'scheisse subject'
            })
            self.assert_error(result, "Update group with German bad word in subject", "inappropriate")
       
        # Test 9: Report group
        if group1_id:
            result = report_group(self.db_connector, group1_id)
            self.assert_success(result, "Report group")
            if result.get('status') == 'success':
                reports = result['data']['reports']
                if reports == 1:
                    print(f"{Colors.GREEN}  ✓ Report count incremented: {reports}{Colors.RESET}")
       
        # Test 10: Report group again
        if group1_id:
            result = report_group(self.db_connector, group1_id)
            self.assert_success(result, "Report group second time")
            if result.get('status') == 'success':
                reports = result['data']['reports']
                if reports == 2:
                    print(f"{Colors.GREEN}  ✓ Report count incremented: {reports}{Colors.RESET}")
       
        # Test 11: Verify database count
        self.verify_db_count('groups', 2, "Verify groups table count")
       
        # Test 12: Verify organiser is auto-added as member
        self.verify_db_count('group_users', 2, "Verify organisers auto-added as members")
       
        return group1_id, group2_id
   
    def test_filter_group_operations(self, user1_id, user2_id, group1_id, group2_id):
        """Test filter_groups with various filter combinations"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}========== FILTER GROUP OPERATIONS =========={Colors.RESET}")
 
        # Test 1: Filter by subject
        result = filter_groups(self.db_connector, subject='Mathematics')
        self.assert_success(result, "Filter groups by subject=Mathematics")
        if result.get('status') == 'success':
            count = result['data']['total']
            if count == 1:
                print(f"{Colors.GREEN}  ✓ Found {count} group with subject=Mathematics{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 1, got {count}{Colors.RESET}")
 
        # Test 2: Filter by type
        result = filter_groups(self.db_connector, type='online')
        self.assert_success(result, "Filter groups by type=online")
        if result.get('status') == 'success':
            count = result['data']['total']
            if count == 1:
                print(f"{Colors.GREEN}  ✓ Found {count} group with type=online{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 1, got {count}{Colors.RESET}")
 
        # Test 3: Filter by class
        result = filter_groups(self.db_connector, class_='FI302')
        self.assert_success(result, "Filter groups by class=FI302")
        if result.get('status') == 'success':
            count = result['data']['total']
            if count == 1:
                print(f"{Colors.GREEN}  ✓ Found {count} group with class=FI302{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 1, got {count}{Colors.RESET}")
 
        # Test 4: Filter by status
        result = filter_groups(self.db_connector, status='active')
        self.assert_success(result, "Filter groups by status=active")
        if result.get('status') == 'success':
            count = result['data']['total']
            if count >= 1:
                print(f"{Colors.GREEN}  ✓ Found {count} active group(s){Colors.RESET}")
 
        # Test 5: Filter by location
        result = filter_groups(self.db_connector, location='Teams')
        self.assert_success(result, "Filter groups by location=Teams")
        if result.get('status') == 'success':
            count = result['data']['total']
            if count == 1:
                print(f"{Colors.GREEN}  ✓ Found {count} group at location=Teams{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 1, got {count}{Colors.RESET}")
 
        # Test 6: Filter by organiser_id
        result = filter_groups(self.db_connector, organiser_id=user1_id)
        self.assert_success(result, "Filter groups by organiser_id (user1)")
        if result.get('status') == 'success':
            count = result['data']['total']
            if count == 1:
                print(f"{Colors.GREEN}  ✓ Found {count} group for organiser user1{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 1, got {count}{Colors.RESET}")
 
        # Test 7: Filter has_space=True (groups with free spots)
        result = filter_groups(self.db_connector, has_space=True)
        self.assert_success(result, "Filter groups with has_space=True")
        if result.get('status') == 'success':
            count = result['data']['total']
            print(f"{Colors.GREEN}  ✓ Found {count} group(s) with free spots{Colors.RESET}")
 
        # Test 8: Combined filter — subject + type
        result = filter_groups(self.db_connector, subject='Mathematics', type='online')
        self.assert_success(result, "Filter groups by subject + type combined")
        if result.get('status') == 'success':
            count = result['data']['total']
            if count == 1:
                print(f"{Colors.GREEN}  ✓ Combined filter returned {count} result{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 1, got {count}{Colors.RESET}")
 
        # Test 9: Filter that matches nothing
        result = filter_groups(self.db_connector, subject='NonExistentSubject')
        self.assert_success(result, "Filter groups with no match returns empty list")
        if result.get('status') == 'success':
            count = result['data']['total']
            if count == 0:
                print(f"{Colors.GREEN}  ✓ Correctly returned 0 results{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 0, got {count}{Colors.RESET}")
 
        # Test 10: Pagination — limit=1
        result = filter_groups(self.db_connector, limit=1, offset=0)
        self.assert_success(result, "Filter groups with limit=1 pagination")
        if result.get('status') == 'success':
            returned = len(result['data']['groups'])
            if returned == 1:
                print(f"{Colors.GREEN}  ✓ Pagination limit=1 returned {returned} group{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 1 group, got {returned}{Colors.RESET}")
 
    def test_membership_operations(self, user1_id, user2_id, group1_id, group2_id):
        """Test group membership operations"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}========== MEMBERSHIP OPERATIONS =========={Colors.RESET}")
       
        # Test 1: Add user2 to group1
        result = add_group_member(self.db_connector, group1_id, {
            'user_id': user2_id
        })
        self.assert_success(result, "Add member to group")
       
        # Test 2: Try to add same user again
        result = add_group_member(self.db_connector, group1_id, {
            'user_id': user2_id
        })
        self.assert_error(result, "Add duplicate member to group", "already a member")
       
        # Test 3: Add non-existent user
        result = add_group_member(self.db_connector, group1_id, {
            'user_id': 99999
        })
        self.assert_error(result, "Add non-existent user to group", "not found")
       
        # Test 4: Add user to non-existent group
        result = add_group_member(self.db_connector, 99999, {
            'user_id': user2_id
        })
        self.assert_error(result, "Add user to non-existent group", "not found")
       
        # Test 5: Verify membership count
        self.verify_db_count('group_users', 3, "Verify group_users count after additions")
       
        # Test 6: Get user groups
        result = get_user_groups(self.db_connector, user1_id)
        self.assert_success(result, "Get user1 groups")
        if result.get('status') == 'success':
            groups_count = result['data']['count']
            if groups_count == 1:
                print(f"{Colors.GREEN}  ✓ User1 is in {groups_count} group{Colors.RESET}")
            else:
                print(f"{Colors.RED}  ✗ Expected 1 group, got {groups_count}{Colors.RESET}")
       
        # Test 7: Remove member from group
        result = remove_group_member(self.db_connector, group1_id, user2_id)
        self.assert_success(result, "Remove member from group")
       
        # Test 8: Try to remove organiser
        result = remove_group_member(self.db_connector, group1_id, user1_id)
        self.assert_error(result, "Remove organiser from group", "organiser")
       
        # Test 9: Try to remove non-member
        result = remove_group_member(self.db_connector, group1_id, user2_id)
        self.assert_error(result, "Remove non-member from group", "not a member")
       
        # Test 10: Verify final membership count
        self.verify_db_count('group_users', 2, "Verify final group_users count")
   
    def test_join_request_operations(self, user1_id, user2_id, group1_id, group2_id):
        """Test join request operations"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}========== JOIN REQUEST OPERATIONS =========={Colors.RESET}")
       
        # Test 1: Create join request
        email_count_before = len(self.sent_emails)
        result = create_beitrittsanfrage(self.db_connector, {
            'user_id': user2_id,
            'group_id': group1_id,
            'message': 'I would like to join this group'
        })
        self.assert_success(result, "Create join request")
        if result.get('status') == 'success':
            self.verify_email_sent(
                email_count_before + 1,
                "Send notification email on join request creation",
                recipient='updated@gso.schule.koeln',
                template_name='notification'
            )
        request1_id = result['data']['id'] if result.get('status') == 'success' else None
       
        # Test 2: Create duplicate join request
        email_count_before = len(self.sent_emails)
        result = create_beitrittsanfrage(self.db_connector, {
            'user_id': user2_id,
            'group_id': group1_id
        })
        self.assert_error(result, "Create duplicate join request", "pending")
       
        self.verify_email_sent(
            email_count_before,
            "No notification email on duplicate join request"
        )
        
        # Test 3: Get all join requests
        result = get_join_requests(self.db_connector)
        self.assert_success(result, "Get all join requests")
        if result.get('status') == 'success':
            count = result['data']['count']
            if count == 1:
                print(f"{Colors.GREEN}  ✓ Found {count} join request{Colors.RESET}")
       
        # Test 4: Get join requests by group
        result = get_join_requests(self.db_connector, group_id=group1_id)
        self.assert_success(result, "Get join requests by group_id")
       
        # Test 5: Get join requests by user
        result = get_join_requests(self.db_connector, user_id=user2_id)
        self.assert_success(result, "Get join requests by user_id")
       
        # Test 6: Get join request by ID
        if request1_id:
            result = get_join_request_by_id(self.db_connector, request1_id)
            self.assert_success(result, "Get join request by ID")
       
        # Test 7: Approve join request
        if request1_id:
            email_count_before = len(self.sent_emails)
            result = approve_join_request(self.db_connector, request1_id)
            self.assert_success(result, "Approve join request")

            if result.get('status') == 'success':
                # Verify user was added to group
                self.verify_db_count('group_users', 3, "Verify user added to group after approval")

                # Verify email sent to requester about approval
                self.verify_email_sent(
                    email_count_before + 1,
                    "Send notification email on join request approval",
                    recipient='test2@gso.schule.koeln',
                    subject='Join Request Approved',
                    body_contains=f'group {group1_id}'
                )
       
        # Test 8: Create new join request for rejection test
        email_count_before = len(self.sent_emails)
        result = create_beitrittsanfrage(self.db_connector, {
            'user_id': user1_id,
            'group_id': group2_id,
            'message': 'Testing rejection'
        })
        self.assert_success(result, "Create join request for rejection test")
        if result.get('status') == 'success':
            self.verify_email_sent(
                email_count_before + 1,
                "Send notification email for second join request",
                recipient='test2@gso.schule.koeln',
                template_name='notification'
            )
        request2_id = result['data']['id'] if result.get('status') == 'success' else None
       
        # Test 9: Reject join request
        if request2_id:
            result = reject_join_request(self.db_connector, request2_id)
            self.assert_success(result, "Reject join request")
           
            # Verify user was NOT added to group
            self.verify_db_count('group_users', 3, "Verify user NOT added after rejection")
       
        # Test 10: Try to approve already approved request
        if request1_id:
            result = approve_join_request(self.db_connector, request1_id)
            self.assert_error(result, "Approve already approved request", "already")
       
        # Test 11: Create and delete join request
        result = create_beitrittsanfrage(self.db_connector, {
            'user_id': user1_id,
            'group_id': group2_id
        })
        if result.get('status') == 'success':
            request3_id = result['data']['id']
            email_count_before = len(self.sent_emails)
            result = delete_beitrittsanfrage(self.db_connector, request3_id)
            self.assert_success(result, "Delete join request")
            if result.get('status') == 'success':
                self.verify_email_sent(
                    email_count_before + 1,
                    "Send notification email on join request deletion",
                    recipient='updated@gso.schule.koeln',
                    subject='Join Request Deleted',
                    body_contains='has been deleted'
                )
       
        # Test 12: Verify final join_requests count
        self.verify_db_count('join_requests', 1, "Verify final join_requests count")
   
    def test_max_users_constraint(self, user1_id, user2_id):
        """Test max_users constraint and group full scenarios"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}========== MAX USERS CONSTRAINT =========={Colors.RESET}")
       
        # Create a group with max_users = 2 (organiser will be auto-added)
        result = create_group(self.db_connector, {
            'organiser_id': user1_id,
            'title': 'Limited Group',
            'max_users': 2
        })
        self.assert_success(result, "Create group with max_users=2")
        limited_group_id = result['data']['id'] if result.get('status') == 'success' else None
       
        if limited_group_id:
            # Add one more user (should succeed - group will be at capacity)
            result = add_group_member(self.db_connector, limited_group_id, {
                'user_id': user2_id
            })
            self.assert_success(result, "Add member to group (reaches max)")
           
            # Create a third user
            result = create_user(self.db_connector, {
                'email': 'user3@gso.schule.koeln',
                'password': 'password'
            })
            user3_id = result['data']['id'] if result.get('status') == 'success' else None
           
            if user3_id:
                # Try to add third user (should fail - group is full)
                result = add_group_member(self.db_connector, limited_group_id, {
                    'user_id': user3_id
                })
                self.assert_error(result, "Add member to full group", "full")
               
                # Try to reduce max_users below current count
                result = update_group(self.db_connector, limited_group_id, {
                    'max_users': 1
                })
                self.assert_error(result, "Reduce max_users below current count", "cannot")
   
    def test_delete_operations(self, user1_id, user2_id, group1_id, group2_id):
        """Test delete operations and cascades"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}========== DELETE OPERATIONS =========={Colors.RESET}")
       
        # Test 1: Try to delete user who is organiser
        result = delete_user(self.db_connector, user1_id, executing_user_email='updated@gso.schule.koeln')
        self.assert_error(result, "Delete user who is organiser", "organiser")
       
        # Test 2: Delete group
        if group2_id:
            result = delete_group(self.db_connector, group2_id)
            self.assert_success(result, "Delete group")
           
            # Verify cascade delete of memberships
            conn = self.db_connector.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM group_users WHERE group_id = ?", (group2_id,))
            count = cursor.fetchone()[0]
            conn.close()
           
            if count == 0:
                self.passed += 1
                print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} Cascade delete of group memberships")
            else:
                self.failed += 1
                print(f"{Colors.RED}✗ FAIL:{Colors.RESET} Cascade delete failed, {count} memberships remain")
       
        # Test 3: Delete non-existent group
        result = delete_group(self.db_connector, 99999)
        self.assert_error(result, "Delete non-existent group", "not found")
       
        # Test 4: Delete all groups user1 organizes
        # Need to delete group1 and the limited group from max_users test
        conn = self.db_connector.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM groups WHERE organiser_id = ?", (user1_id,))
        user1_groups = cursor.fetchall()
        conn.close()
       
        for (gid,) in user1_groups:
            result = delete_group(self.db_connector, gid)
            if result.get('status') == 'success':
                print(f"{Colors.GREEN}  ✓ Deleted group {gid} organized by user1{Colors.RESET}")
       
        # Now delete user1
        result = delete_user(self.db_connector, user1_id, executing_user_email='updated@gso.schule.koeln')
        self.assert_success(result, "Delete user after removing organiser role")
       
        # Test 5: Delete non-existent user
        conn = self.db_connector.connect()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = 'teacher' WHERE email = ?", ('test2@gso.schule.koeln',))
        conn.commit()
        conn.close()
 
        result = delete_user(self.db_connector, 99999, executing_user_email='test2@gso.schule.koeln')
        self.assert_error(result, "Delete non-existent user", "not found")
       
        # Test 6: Try to delete another user without proper role (student/normal user)
        # Create a new user to test insufficient permissions
        result = create_user(self.db_connector, {
            'email': 'student@gso.schule.koeln',
            'password': 'password123'
        })
        student_id = result['data']['id'] if result.get('status') == 'success' else None
       
        if student_id:
            # student tries to delete test2@example.com (now a teacher)
            # This should fail because student has no special role and is not deleting themselves
            result = delete_user(self.db_connector, user2_id, executing_user_email='student@gso.schule.koeln')
            self.assert_error(result, "Delete other user without admin/teacher role", "berechtigt")
   
    def test_edge_cases(self):
        """Test various edge cases and error handling"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}========== EDGE CASES =========={Colors.RESET}")
       
        # Test 1: Empty/null values
        result = create_user(self.db_connector, {})
        self.assert_error(result, "Create user with empty data", "required")
       
        # Test 2: Very long strings
        result = create_user(self.db_connector, {
            'email': 'a' * 500 + '@gso.schule.koeln',
            'password': 'password'
        })
        # This might succeed or fail depending on DB constraints
        # Just verify it doesn't crash
        print(f"{Colors.GREEN}✓ PASS:{Colors.RESET} Handle very long email without crashing")
        self.passed += 1
       
        # Test 3: Special characters in data
        result = create_user(self.db_connector, {
            'email': 'test+special@gso.schule.koeln',
            'password': 'p@$$w0rd!#%'
        })
        self.assert_success(result, "Create user with special characters")
       
        # Test 4: Pagination edge cases
        result = get_all_users(self.db_connector, limit=0, offset=0)
        self.assert_error(result, "Get users with limit=0", "at least 1")
       
        result = get_all_users(self.db_connector, limit=10, offset=-1)
        self.assert_error(result, "Get users with negative offset", ">=")
   
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
        log(f"API test summary: passed={self.passed}, failed={self.failed}, total={total}, pass_rate={pass_rate:.1f}%")
       
        if self.failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.RESET}")
            for name, passed, error in self.test_results:
                if not passed:
                    print(f"  {Colors.RED}✗{Colors.RESET} {name}")
                    if error:
                        print(f"    {Colors.RED}{error}{Colors.RESET}")
       
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 50}{Colors.RESET}\n")
       
        return self.failed == 0
   
    def run_all_tests(self):
        """Run all test suites"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 50}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}LERNGRUPPENTOOL API TEST SUITE{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 50}{Colors.RESET}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
       
        try:
            self.setup()
           
            # Run test suites in order
            user1_id, user2_id = self.test_user_operations()
           
            if user1_id and user2_id:
                group1_id, group2_id = self.test_group_operations(user1_id, user2_id)
               
                if group1_id and group2_id:
                    self.test_filter_group_operations(user1_id, user2_id, group1_id, group2_id)
                    self.test_membership_operations(user1_id, user2_id, group1_id, group2_id)
                    self.test_join_request_operations(user1_id, user2_id, group1_id, group2_id)
                    self.test_max_users_constraint(user1_id, user2_id)
                    self.test_delete_operations(user1_id, user2_id, group1_id, group2_id)
           
            self.test_edge_cases()
           
            success = self.print_summary()
           
            self.teardown()
           
            return 0 if success else 1
           
        except Exception as e:
            log(f"Fatal error in API test suite: {str(e)}", "error")
            print(f"\n{Colors.RED}{Colors.BOLD}FATAL ERROR:{Colors.RESET} {str(e)}")
            import traceback
            traceback.print_exc()
            self.teardown()
            return 1
 
 
if __name__ == '__main__':
    tester = APITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)
 
 