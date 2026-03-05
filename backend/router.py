from flask import request, jsonify, g
from tools.auth import require_role

from modules.user.create_user import create_user as create_user_func, verify_user_email as verify_user_email_func
from modules.user.get_user import get_user as get_user_func, get_all_users as get_all_users_func
from modules.user.update_user import update_user as update_user_func
from modules.user.delete_user import delete_user as delete_user_func
from modules.user.login_user import login_user as login_user_func
from modules.user.get_user_groups import get_user_groups as get_user_groups_func
from modules.group.create_group import create_group as create_group_func
from modules.group.get_all_groups import get_all_groups as get_all_groups_func
from modules.group.filter_groups import filter_groups as filter_groups_func
from modules.group.update_group import update_group as update_group_func
from modules.group.delete_group import delete_group as delete_group_func
from modules.group.report_group import report_group as report_group_func

from modules.group_membership.add_member import add_group_member as add_member_func
from modules.group_membership.remove_member import remove_group_member as remove_member_func
from modules.group_membership.get_member_count import get_member_count as get_member_count_func

from modules.join_group_request.create_join_request import create_beitrittsanfrage as create_request_func
from modules.join_group_request.get_join_request import get_join_requests as get_requests_func, get_join_request_by_id as get_request_by_id_func
from modules.join_group_request.delete_join_request import delete_beitrittsanfrage as delete_request_func
from modules.join_group_request.approve_join_request import approve_join_request as approve_request_func, reject_join_request as reject_request_func


def register_routes(app, db_connector):
    @app.route('/api/users', methods=['POST'])
    def create_user():
        data = request.get_json()
        return jsonify(create_user_func(db_connector, data))

    @app.route('/api/users/verify-email', methods=['GET'])
    def verify_user_email():
        token = request.args.get('token', default=None, type=str)
        email = request.args.get('email', default=None, type=str)
        return jsonify(verify_user_email_func(db_connector, token, email))

    @app.route('/api/users', methods=['GET'])
    @require_role(db_connector, 'teacher')
    def get_all_users():
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        search = request.args.get('search', default=None, type=str)
        return jsonify(get_all_users_func(db_connector, limit, offset, search))

    @app.route('/api/users/<int:user_id>', methods=['GET'])
    @require_role(db_connector, 'user')
    def get_user(user_id):
        return jsonify(get_user_func(db_connector, user_id))

    @app.route('/api/users/<int:user_id>', methods=['PATCH'])
    @require_role(db_connector, 'user')
    def update_user(user_id):
        data = request.get_json()
        return jsonify(update_user_func(db_connector, user_id, data))

    @app.route('/api/users/<int:user_id>', methods=['DELETE'])
    @require_role(db_connector, 'user')
    def delete_user(user_id, executing_user_email=None):
        authenticated_email = g.auth_user.get('email') if hasattr(g, 'auth_user') else executing_user_email
        result = delete_user_func(db_connector, user_id, executing_user_email=authenticated_email)
        if result.get('status') == 'success':
            return '', 204
        return jsonify(result), 400

    @app.route('/api/users/login', methods=['POST'])
    def login_user():
        data = request.get_json()
        return jsonify(login_user_func(db_connector, data))

    @app.route('/api/users/<int:user_id>/groups', methods=['GET'])
    @require_role(db_connector, 'user')
    def get_user_groups(user_id):
        role = request.args.get('role', default=None, type=str)
        return jsonify(get_user_groups_func(db_connector, user_id, role))

    @app.route('/api/groups', methods=['POST'])
    @require_role(db_connector, 'user')
    def create_group():
        data = request.get_json()
        return jsonify(create_group_func(db_connector, data))

    @app.route('/api/groups', methods=['GET'])
    @require_role(db_connector, 'user')
    def get_all_groups():
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        search = request.args.get('search', default=None, type=str)
        return jsonify(get_all_groups_func(db_connector, limit, offset, search))

    @app.route('/api/groups/filter', methods=['GET'])
    @require_role(db_connector, 'user')
    def filter_groups():
        subject = request.args.get('subject', default=None, type=str)
        type_ = request.args.get('type', default=None, type=str)
        class_ = request.args.get('class', default=None, type=str)
        status = request.args.get('status', default=None, type=str)
        location = request.args.get('location', default=None, type=str)
        organiser_id = request.args.get('organiser_id', default=None, type=int)
        has_space_raw = request.args.get('has_space', default=None, type=str)
        has_space = None if has_space_raw is None else has_space_raw.lower() == 'true'
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        return jsonify(filter_groups_func(
            db_connector,
            subject=subject,
            type=type_,
            class_=class_,
            status=status,
            location=location,
            has_space=has_space,
            organiser_id=organiser_id,
            limit=limit,
            offset=offset,
        ))

    @app.route('/api/groups/<int:group_id>', methods=['PATCH'])
    @require_role(db_connector, 'user')
    def update_group(group_id):
        data = request.get_json()
        return jsonify(update_group_func(db_connector, group_id, data))

    @app.route('/api/groups/<int:group_id>', methods=['DELETE'])
    @require_role(db_connector, 'user')
    def delete_group(group_id):
        result = delete_group_func(db_connector, group_id)
        if result.get('status') == 'success':
            return '', 204
        return jsonify(result), 400

    @app.route('/api/groups/<int:group_id>/report', methods=['POST'])
    @require_role(db_connector, 'user')
    def report_group(group_id):
        data = request.get_json()
        return jsonify(report_group_func(db_connector, group_id, data))

    @app.route('/api/groups/<int:group_id>/members/count', methods=['GET'])
    @require_role(db_connector, 'user')
    def get_group_member_count(group_id):
        return jsonify(get_member_count_func(db_connector, group_id))

    @app.route('/api/groups/<int:group_id>/members', methods=['POST'])
    @require_role(db_connector, 'user')
    def add_group_member(group_id):
        data = request.get_json()
        return jsonify(add_member_func(db_connector, group_id, data))

    @app.route('/api/groups/<int:group_id>/members/<int:user_id>', methods=['DELETE'])
    @require_role(db_connector, 'user')
    def remove_group_member(group_id, user_id):
        result = remove_member_func(db_connector, group_id, user_id)
        if result.get('status') == 'success':
            return '', 204
        return jsonify(result), 400

    @app.route('/api/join-requests', methods=['POST'])
    @require_role(db_connector, 'user')
    def create_join_request():
        data = request.get_json()
        return jsonify(create_request_func(db_connector, data))

    @app.route('/api/join-requests', methods=['GET'])
    @require_role(db_connector, 'user')
    def get_join_requests():
        group_id = request.args.get('group_id', default=None, type=int)
        user_id = request.args.get('user_id', default=None, type=int)
        status = request.args.get('status', default=None, type=str)
        return jsonify(get_requests_func(db_connector, group_id, user_id, status))

    @app.route('/api/join-requests/<int:request_id>', methods=['GET'])
    @require_role(db_connector, 'user')
    def get_join_request(request_id):
        return jsonify(get_request_by_id_func(db_connector, request_id))

    @app.route('/api/join-requests/<int:request_id>', methods=['DELETE'])
    @require_role(db_connector, 'user')
    def delete_join_request(request_id):
        result = delete_request_func(db_connector, request_id)
        if result.get('status') == 'success':
            return '', 204
        return jsonify(result), 400

    @app.route('/api/join-requests/<int:request_id>/approve', methods=['POST'])
    @require_role(db_connector, 'user')
    def approve_join_request(request_id):
        return jsonify(approve_request_func(db_connector, request_id))

    @app.route('/api/join-requests/<int:request_id>/reject', methods=['POST'])
    @require_role(db_connector, 'user')
    def reject_join_request(request_id):
        return jsonify(reject_request_func(db_connector, request_id))