import time

from core.chat_blob import ChatBlob
from core.command_param_types import NamedParameters, Character
from core.conn import Conn
from core.decorators import instance, command, event
from core.logger import Logger
from core.public_channel_service import PublicChannelService
from core.standard_message import StandardMessage
from modules.core.org_members.org_member_controller import OrgMemberController


@instance()
class OrgActivityController:
    def __init__(self):
        self.logger = Logger(__name__)

    def inject(self, registry):
        self.bot = registry.get_instance("bot")
        self.db = registry.get_instance("db")
        self.util = registry.get_instance("util")
        self.text = registry.get_instance("text")
        self.character_service = registry.get_instance("character_service")
        self.command_alias_service = registry.get_instance("command_alias_service")

    def start(self):
        self.db.exec("CREATE TABLE IF NOT EXISTS org_activity (id INT PRIMARY KEY AUTO_INCREMENT, actor_char_id INT NOT NULL, actee_char_id INT NOT NULL, "
                     "action VARCHAR(20) NOT NULL, created_at INT NOT NULL, org_id INT NOT NULL)")

        self.command_alias_service.add_alias("orghistory", "orgactivity")

    @command(command="orgactivity", params=[Character("char", is_optional=True), NamedParameters(["action", "page"])], access_level="org_member",
             description="Show org member activity")
    def orgactivity_cmd(self, request, char, named_params):
        page_size = 20
        page_number = int(named_params.page or "1")

        params = []
        filter_sql = "WHERE 1=1"
        if char:
            if not char.char_id:
                return StandardMessage.char_not_found(char.name)
            else:
                filter_sql += " AND (o.actor_char_id = ? OR o.actee_char_id = ?)"
                params.append(char.char_id)
                params.append(char.char_id)

        if named_params.action:
            named_params.action = named_params.action.lower()
            filter_sql += " AND o.action LIKE ?"
            params.append(named_params.action)

        offset, limit = self.util.get_offset_limit(page_size, page_number)
        params.append(offset)
        params.append(limit)

        sql = f"""
            SELECT
                p1.name AS actor,
                p2.name AS actee, o.action,
                o.created_at,
                o.org_id
            FROM
                org_activity o
                LEFT JOIN player p1 ON o.actor_char_id = p1.char_id
                LEFT JOIN player p2 ON o.actee_char_id = p2.char_id
            {filter_sql}
            ORDER BY
                o.created_at DESC
            LIMIT ?, ?
        """
        data = self.db.query(sql, params)

        command_str = "orgactivity"
        if char:
            command_str += " " + char.name
        if named_params.action:
            command_str += " --action=" + named_params.action

        blob = self.text.get_paging_links(command_str, page_number, len(data) == page_size) + "\n\n"
        for row in data:
            blob += self.format_org_action(row) + "\n"

        title = "Org Activity"
        if char:
            title += " for " + char.name
        if named_params.action:
            title += " [" + named_params.action + "]"

        return ChatBlob(title, blob)

    @event(PublicChannelService.ORG_MSG_EVENT, "Record org member activity", is_system=True)
    def org_msg_event(self, event_type, event_data):
        ext_msg = event_data.extended_message
        org_id = event_data.conn.org_id
        if [ext_msg.category_id, ext_msg.instance_id] == OrgMemberController.LEFT_ORG:
            self.save_activity(ext_msg.params[0], ext_msg.params[0], "left", org_id)
        elif [ext_msg.category_id, ext_msg.instance_id] == OrgMemberController.KICKED_FROM_ORG:
            self.save_activity(ext_msg.params[0], ext_msg.params[1], "kicked", org_id)
        elif [ext_msg.category_id, ext_msg.instance_id] == OrgMemberController.INVITED_TO_ORG:
            self.save_activity(ext_msg.params[0], ext_msg.params[1], "invited", org_id)
        elif [ext_msg.category_id, ext_msg.instance_id] == OrgMemberController.KICKED_INACTIVE_FROM_ORG:
            self.save_activity(ext_msg.params[0], ext_msg.params[1], "removed", org_id)
        elif [ext_msg.category_id, ext_msg.instance_id] == OrgMemberController.KICKED_ALIGNMENT_CHANGED:
            self.save_activity(ext_msg.params[0], ext_msg.params[0], "alignment changed", org_id)
        elif [ext_msg.category_id, ext_msg.instance_id] == OrgMemberController.JOINED_ORG:
            self.save_activity(ext_msg.params[0], ext_msg.params[0], "joined", org_id)

    def save_activity(self, actor, actee, action, org_id):
        actor_id = self.character_service.resolve_char_to_id(actor)
        actee_id = self.character_service.resolve_char_to_id(actee) if actee else 0

        if not actor_id:
            self.logger.error("Could not get char_id for actor '%s'" % actor)

        if not actee_id:
            self.logger.error("Could not get char_id for actee '%s'" % actee)

        t = int(time.time())
        self.db.exec("INSERT INTO org_activity (actor_char_id, actee_char_id, action, created_at, org_id) VALUES (?, ?, ?, ?, ?)",
                     [actor_id, actee_id, action, t, org_id])

    def format_org_action(self, row):
        org_name = self.get_org_name(row.org_id)
        created_at_str = self.util.format_datetime(row.created_at)
        if row.action == "left" or row.action == "alignment changed" or row.action == "joined":
            return f"<highlight>{row.actor}</highlight> {row.action}. [{org_name}] {created_at_str}"
        else:
            return f"<highlight>{row.actor}</highlight> {row.action} <highlight>{row.actee}</highlight>. [{org_name}] {created_at_str}"

    def get_org_name(self, org_id):
        conn: Conn = self.bot.get_conn_by_org_id(org_id)
        if conn:
            return conn.get_org_name()
        else:
            return f"UnknownOrg({org_id})"
