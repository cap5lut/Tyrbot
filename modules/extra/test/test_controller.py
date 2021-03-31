from core.aochat import server_packets
from core.command_param_types import Int, Const, Options, Character, Any
from core.decorators import instance, command
from core.public_channel_service import PublicChannelService
from modules.core.org_members.org_member_controller import OrgMemberController
from modules.standard.tower.tower_controller import TowerController


@instance()
class TestController:
    def inject(self, registry):
        self.bot = registry.get_instance("bot")
        self.pork_service = registry.get_instance("pork_service")

    @command(command="test", params=[Const("massmsg"), Int("num_tells")], access_level="superadmin",
             description="Test sending tells via mass messaging")
    def test_command(self, request, _, num_tells):
        for i in range(0, num_tells):
            msg = "Test " + str(i)
            # request.reply(msg)
            self.bot.send_mass_message(request.sender.char_id, msg)

    @command(command="test", params=[Const("cloak"), Options(["on", "off"])], access_level="superadmin",
             description="Trigger raising or lowering cloak")
    def test_cloak_status_command(self, request, _, cloak_status):
        ext_msg = self.ext_message_as_string(1001, 1, [("s", request.sender.name), ("s", cloak_status)])

        packet = server_packets.PublicChannelMessage(request.conn.org_channel_id, request.sender.char_id, ext_msg, "\0")
        self.bot.incoming_queue.put((request.conn, packet))

    @command(command="test", params=[Const("citytargetted")], access_level="superadmin",
             description="Trigger city targetted by aliens")
    def test_citytargetted_command(self, request, _):
        ext_msg = self.ext_message_as_string(1001, 3, [("s", "Antarctica")])

        packet = server_packets.PublicChannelMessage(request.conn.org_channel_id, request.sender.char_id, ext_msg, "\0")
        self.bot.incoming_queue.put((request.conn, packet))

    @command(command="test", params=[Const("attack"), Character("attack_char"), Any("defender_faction"), Any("defend_org_name")], access_level="superadmin",
             description="Trigger tower attack")
    def test_towerattack_cmd(self, request, _, attacker, def_faction, def_org_name):
        playfield_name = "Perpetual Wastelands"
        x_coords = "123"
        y_coords = "456"

        char_info = self.pork_service.get_character_info(attacker.name)
        if not char_info:
            return f"Could not retrieve character info for <highlight>{attacker.name}</highlight>."
        elif not char_info.org_name:
            f"{attacker.name} just attacked the {def_faction} organization {def_org_name.lower()}'s tower in {playfield_name} at location ({x_coords}, {y_coords})."
        else:
            # The %s organization %s just entered a state of war! %s attacked the %s organization %s's tower in %s at location (%d,%d).
            ext_msg = self.ext_message_as_string(506, 12753364, [("s", char_info.faction), ("s", char_info.org_name), ("s", char_info.name),
                                                                 ("s", def_faction), ("s", def_org_name),
                                                                 ("s", playfield_name), ("s", x_coords), ("s", y_coords)])
            packet = server_packets.PublicChannelMessage(TowerController.ALL_TOWERS_ID, 0, ext_msg, "\0")
            self.bot.incoming_queue.put((request.conn, packet))

    @command(command="test", params=[Const("org"), Const("leave"), Character("char")], access_level="superadmin",
             description="Trigger org left")
    def test_org_leave_cmd(self, request, _1, _2, char):
        if not char.char_id:
            return "Character <highlight>%s</highlight> does not exist." % char.name

        category_id, instance_id = OrgMemberController.LEFT_ORG
        ext_msg = self.ext_message_as_string(category_id, instance_id, [("s", char.name)])
        packet = server_packets.PublicChannelMessage(PublicChannelService.ORG_MSG_CHANNEL_ID, 0, ext_msg, "\0")
        self.bot.incoming_queue.put((request.conn, packet))

    @command(command="test", params=[Const("org"), Const("kick"), Character("kicked_by_char"), Character("kicked_char")], access_level="superadmin",
             description="Trigger org kick")
    def test_org_kicked_cmd(self, request, _1, _2, kicked_by_char, kicked_char):
        if not kicked_by_char.char_id:
            return "Character <highlight>%s</highlight> does not exist." % kicked_by_char.name

        if not kicked_char.char_id:
            return "Character <highlight>%s</highlight> does not exist." % kicked_char.name

        category_id, instance_id = OrgMemberController.KICKED_FROM_ORG
        ext_msg = self.ext_message_as_string(category_id, instance_id, [("s", kicked_by_char.name), ("s", kicked_char.name)])
        packet = server_packets.PublicChannelMessage(PublicChannelService.ORG_MSG_CHANNEL_ID, 0, ext_msg, "\0")
        self.bot.incoming_queue.put((request.conn, packet))

    @command(command="test", params=[Const("org"), Const("invite"), Character("invited_by_char"), Character("invited_char")], access_level="superadmin",
             description="Trigger org invite")
    def test_org_invite_cmd(self, request, _1, _2, invited_by_char, invited_char):
        if not invited_by_char.char_id:
            return "Character <highlight>%s</highlight> does not exist." % invited_by_char.name

        if not invited_char.char_id:
            return "Character <highlight>%s</highlight> does not exist." % invited_char.name

        category_id, instance_id = OrgMemberController.INVITED_TO_ORG
        ext_msg = self.ext_message_as_string(category_id, instance_id, [("s", invited_by_char.name), ("s", invited_char.name)])
        packet = server_packets.PublicChannelMessage(PublicChannelService.ORG_MSG_CHANNEL_ID, 0, ext_msg, "\0")
        self.bot.incoming_queue.put((request.conn, packet))

    @command(command="test", params=[Const("org"), Const("remove"), Character("removed_by_char"), Character("removed_char")], access_level="superadmin",
             description="Trigger org remove (remotely)")
    def test_org_remove_cmd(self, request, _1, _2, removed_by_char, removed_char):
        if not removed_by_char.char_id:
            return "Character <highlight>%s</highlight> does not exist." % removed_by_char.name

        if not removed_char.char_id:
            return "Character <highlight>%s</highlight> does not exist." % removed_char.name

        category_id, instance_id = OrgMemberController.KICKED_INACTIVE_FROM_ORG
        ext_msg = self.ext_message_as_string(category_id, instance_id, [("s", removed_by_char.name), ("s", removed_char.name)])
        packet = server_packets.PublicChannelMessage(PublicChannelService.ORG_MSG_CHANNEL_ID, 0, ext_msg, "\0")
        self.bot.incoming_queue.put((request.conn, packet))

    @command(command="test", params=[Const("org"), Const("alignment_change"), Character("char")], access_level="superadmin",
             description="Trigger org left due to alignment changed")
    def test_org_alignment_change_cmd(self, request, _1, _2, char):
        if not char.char_id:
            return "Character <highlight>%s</highlight> does not exist." % char.name

        category_id, instance_id = OrgMemberController.KICKED_ALIGNMENT_CHANGED
        ext_msg = self.ext_message_as_string(category_id, instance_id, [("s", char.name)])
        packet = server_packets.PublicChannelMessage(PublicChannelService.ORG_MSG_CHANNEL_ID, 0, ext_msg, "\0")
        self.bot.incoming_queue.put((request.conn, packet))

    @command(command="test", params=[Const("org"), Const("join"), Character("char")], access_level="superadmin",
             description="Trigger org joined")
    def test_org_join_cmd(self, request, _1, _2, char):
        if not char.char_id:
            return "Character <highlight>%s</highlight> does not exist." % char.name

        category_id, instance_id = OrgMemberController.JOINED_ORG
        ext_msg = self.ext_message_as_string(category_id, instance_id, [("s", char.name)])
        packet = server_packets.PublicChannelMessage(PublicChannelService.ORG_MSG_CHANNEL_ID, 0, ext_msg, "\0")
        self.bot.incoming_queue.put((request.conn, packet))

    def ext_message_as_string(self, category_id, instance_id, params):
        ext_msg = self.bot.mmdb_parser.write_ext_message(category_id, instance_id, params)
        return ext_msg.decode("utf-8")