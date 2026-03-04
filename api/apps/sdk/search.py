#
#  Copyright 2025 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
SDK API endpoints for AI Search app CRUD operations.
Uses @token_required for API key authentication (Authorization: Bearer <api_key>).
Auto-registered at /api/v1/search/* by the blueprint scanner.
"""

from quart import request

from api.constants import DATASET_NAME_LIMIT
from api.db.db_models import DB
from api.db.services import duplicate_name
from api.db.services.search_service import SearchService
from api.db.services.user_service import TenantService, UserTenantService
from common.misc_utils import get_uuid
from common.constants import RetCode, StatusEnum
from api.utils.api_utils import (
    get_error_argument_result,
    get_error_data_result,
    get_result,
    token_required,
    server_error_response,
)


@manager.route("/searchs", methods=["POST"])  # noqa: F821
@token_required
async def create(tenant_id):
    """
    Create a new AI Search app.
    ---
    tags:
      - Search
    security:
      - ApiKeyAuth: []
    parameters:
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
      - in: body
        name: body
        description: Search app creation parameters.
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              description: Search app name (required).
            description:
              type: string
              description: Optional search app description.
    responses:
      200:
        description: Successful operation.
        schema:
          type: object
          properties:
            data:
              type: object
    """
    req = await request.get_json()
    if not req:
        return get_error_argument_result(message="Request body is required")

    # Validate required name field
    search_name = req.get("name")
    description = req.get("description", "")

    if not search_name or not isinstance(search_name, str):
        return get_error_argument_result(message="Search name is required and must be a string")
    if search_name.strip() == "":
        return get_error_data_result(message="Search name can't be empty.")
    if len(search_name.encode("utf-8")) > 255:
        return get_error_data_result(message=f"Search name length is {len(search_name)} which is larger than 255.")

    # Verify tenant exists
    e, _ = TenantService.get_by_id(tenant_id)
    if not e:
        return get_error_data_result(message="Authorized identity.")

    # Deduplicate name
    search_name = search_name.strip()
    search_name = duplicate_name(SearchService.query, name=search_name, tenant_id=tenant_id, status=StatusEnum.VALID.value)

    # Build record
    req["id"] = get_uuid()
    req["name"] = search_name
    req["description"] = description
    req["tenant_id"] = tenant_id
    req["created_by"] = tenant_id

    with DB.atomic():
        try:
            if not SearchService.save(**req):
                return get_error_data_result()
            return get_result(data={"search_id": req["id"]})
        except Exception as e:
            return server_error_response(e)


@manager.route("/searchs/<search_id>", methods=["PUT"])  # noqa: F821
@token_required
async def update(tenant_id, search_id):
    """
    Update an existing AI Search app.
    ---
    tags:
      - Search
    security:
      - ApiKeyAuth: []
    parameters:
      - in: path
        name: search_id
        type: string
        required: true
        description: ID of the search app to update.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
      - in: body
        name: body
        description: Search app update parameters.
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: Updated name.
            description:
              type: string
              description: Updated description.
            search_config:
              type: object
              description: Updated search configuration.
    responses:
      200:
        description: Successful operation.
        schema:
          type: object
    """
    req = await request.get_json()
    if not req:
        return get_error_argument_result(message="Request body is required")

    # Verify permission
    if not SearchService.accessible4deletion(search_id, tenant_id):
        return get_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)

    try:
        # Get existing search app
        search_apps = SearchService.query(tenant_id=tenant_id, id=search_id)
        if not search_apps:
            return get_error_data_result(message=f"Cannot find search {search_id}")
        search_app = search_apps[0]

        # Validate name if provided
        if "name" in req:
            name = req["name"]
            if not isinstance(name, str) or name.strip() == "":
                return get_error_data_result(message="Search name must be a non-empty string.")
            if len(name.encode("utf-8")) > DATASET_NAME_LIMIT:
                return get_error_data_result(message=f"Search name length exceeds limit of {DATASET_NAME_LIMIT}")
            req["name"] = name.strip()

            # Check for duplicate name
            if req["name"].lower() != search_app.name.lower():
                existing = SearchService.query(name=req["name"], tenant_id=tenant_id, status=StatusEnum.VALID.value)
                if len(existing) >= 1:
                    return get_error_data_result(message="Duplicated search name.")

        # Merge search_config if provided
        if "search_config" in req:
            current_config = search_app.search_config or {}
            new_config = req["search_config"]
            if not isinstance(new_config, dict):
                return get_error_data_result(message="search_config must be a JSON object")
            req["search_config"] = {**current_config, **new_config}

        # Remove fields that should not be updated
        req.pop("id", None)
        req.pop("created_by", None)
        req.pop("create_time", None)
        req.pop("update_time", None)
        req.pop("create_date", None)
        req.pop("update_date", None)
        req.pop("tenant_id", None)

        # Update the record
        updated = SearchService.update_by_id(search_id, req)
        if not updated:
            return get_error_data_result(message="Failed to update search")

        # Return updated record
        e, updated_search = SearchService.get_by_id(search_id)
        if not e:
            return get_error_data_result(message="Failed to fetch updated search")

        return get_result(data=updated_search.to_dict())

    except Exception as e:
        return server_error_response(e)


@manager.route("/searchs/<search_id>", methods=["GET"])  # noqa: F821
@token_required
def detail(tenant_id, search_id):
    """
    Get AI Search app detail.
    ---
    tags:
      - Search
    security:
      - ApiKeyAuth: []
    parameters:
      - in: path
        name: search_id
        type: string
        required: true
        description: ID of the search app.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
    responses:
      200:
        description: Successful operation.
        schema:
          type: object
    """
    try:
        # Check access via tenant ownership
        tenants = UserTenantService.query(user_id=tenant_id)
        for tenant in tenants:
            if SearchService.query(tenant_id=tenant.tenant_id, id=search_id):
                break
        else:
            return get_result(data=False, message="No permission for this operation.", code=RetCode.OPERATING_ERROR)

        # Get detail
        search = SearchService.get_detail(search_id)
        if not search:
            return get_error_data_result(message="Can't find this Search App!")
        return get_result(data=search)

    except Exception as e:
        return server_error_response(e)


@manager.route("/searchs", methods=["GET"])  # noqa: F821
@token_required
def list_search_apps(tenant_id):
    """
    List AI Search apps.
    ---
    tags:
      - Search
    security:
      - ApiKeyAuth: []
    parameters:
      - in: query
        name: keywords
        type: string
        required: false
        description: Search keyword filter.
      - in: query
        name: page
        type: integer
        required: false
        default: 0
        description: Page number.
      - in: query
        name: page_size
        type: integer
        required: false
        default: 0
        description: Items per page.
      - in: query
        name: orderby
        type: string
        required: false
        default: create_time
        description: Field to order by.
      - in: query
        name: desc
        type: boolean
        required: false
        default: true
        description: Order descending.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
    responses:
      200:
        description: Successful operation.
        schema:
          type: object
    """
    keywords = request.args.get("keywords", "")
    page_number = int(request.args.get("page", 0))
    items_per_page = int(request.args.get("page_size", 0))
    orderby = request.args.get("orderby", "create_time")
    desc = request.args.get("desc", "true").lower() != "false"

    try:
        # List search apps for current tenant
        tenants = []
        search_apps, total = SearchService.get_by_tenant_ids(
            tenants, tenant_id, page_number, items_per_page, orderby, desc, keywords
        )
        return get_result(data={"search_apps": search_apps, "total": total})
    except Exception as e:
        return server_error_response(e)


@manager.route("/searchs/<search_id>", methods=["DELETE"])  # noqa: F821
@token_required
def rm(tenant_id, search_id):
    """
    Delete an AI Search app.
    ---
    tags:
      - Search
    security:
      - ApiKeyAuth: []
    parameters:
      - in: path
        name: search_id
        type: string
        required: true
        description: ID of the search app to delete.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
    responses:
      200:
        description: Successful operation.
        schema:
          type: object
    """
    # Verify permission
    if not SearchService.accessible4deletion(search_id, tenant_id):
        return get_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)

    try:
        if not SearchService.delete_by_id(search_id):
            return get_error_data_result(message=f"Failed to delete search App {search_id}")
        return get_result(data=True)
    except Exception as e:
        return server_error_response(e)
