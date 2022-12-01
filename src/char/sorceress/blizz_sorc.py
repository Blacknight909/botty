import keyboard
from char.sorceress import Sorceress
from utils.custom_mouse import mouse
from logger import Logger
from utils.misc import wait, rotate_vec, unit_vector
import random
from pather import Location
import numpy as np
from config import Config
import template_finder
import time
import numpy as np
from health_manager import get_panel_check_paused, set_panel_check_paused
from inventory.personal import inspect_items
from screen import convert_abs_to_monitor, convert_screen_to_abs, grab, convert_abs_to_screen
from target_detect import get_visible_targets, TargetInfo, log_targets

class BlizzSorc(Sorceress):
    def __init__(self, *args, **kwargs):
        Logger.info("Setting up Blizz Sorc")
        super().__init__(*args, **kwargs)
        #Nihlathak Bottom Right
        self._pather.offset_node(505, (50, 200))
        self._pather.offset_node(506, (40, -10))
        #Nihlathak Top Right
        self._pather.offset_node(510, (700, -55))
        self._pather.offset_node(511, (30, -25))
        #Nihlathak Top Left
        self._pather.offset_node(515, (-120, -100))
        self._pather.offset_node(517, (-18, -58))
        #Nihlathak Bottom Left
        self._pather.offset_node(500, (-150, 200))
        self._pather.offset_node(501, (10, -33))

    def _ice_blast(self, cast_pos_abs: tuple[float, float], delay: tuple[float, float] = (0.16, 0.23), spray: float = 10):
        keyboard.send(Config().char["stand_still"], do_release=False)
        if self._skill_hotkeys["ice_blast"]:
            keyboard.send(self._skill_hotkeys["ice_blast"])
        for _ in range(5):
            x = cast_pos_abs[0] + (random.random() * 2*spray - spray)
            y = cast_pos_abs[1] + (random.random() * 2*spray - spray)
            cast_pos_monitor = convert_abs_to_monitor((x, y))
            mouse.move(*cast_pos_monitor)
            mouse.press(button="left")
            wait(delay[0], delay[1])
            mouse.release(button="left")
        keyboard.send(Config().char["stand_still"], do_press=False)

    def _blizzard(self, cast_pos_abs: tuple[float, float], spray: float = 10):
        if not self._skill_hotkeys["blizzard"]:
            raise ValueError("You did not set a hotkey for blizzard!")
        keyboard.send(self._skill_hotkeys["blizzard"])
        x = cast_pos_abs[0] + (random.random() * 2 * spray - spray)
        y = cast_pos_abs[1] + (random.random() * 2 * spray - spray)
        cast_pos_monitor = convert_abs_to_monitor((x, y))
        mouse.move(*cast_pos_monitor)
        click_tries = random.randint(2, 4)
        for _ in range(click_tries):
            mouse.press(button="right")
            wait(0.09, 0.12)
            mouse.release(button="right")

    def _generic_blizz_attack_sequence(
        self,
        default_target_abs: tuple[int, int] = (0, 0),
        min_duration: float = 2,
        max_duration: float = 7,
        target_detect: bool = True,
        default_spray: int = 50,
    ) -> bool:
        start = time.time()
        target_check_count = 1
        while (elapsed := (time.time() - start)) <= max_duration:
            cast_pos_abs = default_target_abs
            spray = default_spray
            if target_detect and (targets := get_visible_targets()):
                Logger.debug("KILLING TARGETS")
                spray = 2
                cast_pos_abs = targets[0].center_abs
                self._blizzard(cast_pos_abs, spray=spray)
                self._ice_blast(cast_pos_abs, spray=spray)
            if elapsed > min_duration and (not target_detect or not targets):
                break
            else:
#                Logger.debug("NO TARGETS FOUND")
                self._blizzard(cast_pos_abs, spray=spray)
            target_check_count += 1
        return True

    def kill_pindle(self) -> bool:
        pindle_pos_abs = convert_screen_to_abs(Config().path["pindle_end"][0])
        cast_pos_abs = [pindle_pos_abs[0] * 0.9, pindle_pos_abs[1] * 0.9]
        for _ in range(int(Config().char["atk_len_pindle"])):
            self._blizzard(cast_pos_abs, spray=11)
            self._ice_blast(cast_pos_abs, spray=11)
            self._blizzard(cast_pos_abs, spray=11)
            self._ice_blast(cast_pos_abs, spray=11)
        # Move to items
        wait(self._cast_duration, self._cast_duration + 0.2)
        self._pather.traverse_nodes_fixed("pindle_end", self)
        return True

    def kill_eldritch(self) -> bool:
        #move up
        pos_m = convert_abs_to_monitor((0, -175))
        self.pre_move()
        self.move(pos_m, force_move=True)
        self._generic_blizz_attack_sequence()
        wait(0.75)
        #move down
        pos_m = convert_abs_to_monitor((0, 85))
        self.pre_move()
        self.move(pos_m, force_move=True)
        self._generic_blizz_attack_sequence()
        #move down
        wait(0.75)
        pos_m = convert_abs_to_monitor((0, 75))
        self.pre_move()
        self.move(pos_m, force_move=True)
        self._generic_blizz_attack_sequence()
        self._pather.traverse_nodes_fixed("eldritch_end", self)
        return True

    def kill_shenk(self) -> bool:
        pos_m = convert_abs_to_monitor((100, 170))
        self.pre_move()
        self.move(pos_m, force_move=True)
        #lower left posistion
        self._pather.traverse_nodes([151], self, timeout=2.5, force_tp=False)
        self._generic_blizz_attack_sequence()
        pos_m = convert_abs_to_monitor((-10, 10))
        self.pre_move()
        self.move(pos_m, force_move=True)
        self._generic_blizz_attack_sequence()
        wait(1.0)
        #teledance 2
        pos_m = convert_abs_to_monitor((150, -240))
        self.pre_move()
        self.move(pos_m, force_move=True)
        #teledance attack 2
        self._generic_blizz_attack_sequence()
        wait(0.3)
        #Shenk Kill
        self._generic_blizz_attack_sequence()
        # Move to items
        self._pather.traverse_nodes((Location.A5_SHENK_SAFE_DIST, Location.A5_SHENK_END), self, timeout=1.4, force_tp=True)
        return True

    def kill_council(self) -> bool:
        # Move inside to the right
        self._pather.traverse_nodes_fixed([(1110, 120)], self)
        self._pather.offset_node(300, (80, -110))
        self._pather.traverse_nodes([300], self, timeout=5.5, force_tp=True)
        self._pather.offset_node(300, (-80, 110))
        # Attack to the left
        self._blizzard((-150, 10), spray=80)
        self._ice_blast((-300, 50), spray=40)
        # Tele back and attack
        pos_m = convert_abs_to_monitor((-50, 200))
        self.pre_move()
        self.move(pos_m, force_move=True)
        self._blizzard((-235, -230), spray=80)
        wait(1.0)
        pos_m = convert_abs_to_monitor((-285, -320))
        self.pre_move()
        self.move(pos_m, force_move=True)
        wait(0.5)
        # Move to far left
        self._pather.offset_node(301, (-80, -50))
        self._pather.traverse_nodes([301], self, timeout=2.5, force_tp=True)
        self._pather.offset_node(301, (80, 50))
        # Attack to RIGHT
        self._blizzard((100, 150), spray=80)
        self._ice_blast((230, 230), spray=20)
        wait(0.5)
        self._blizzard((310, 260), spray=80)
        wait(1.0)
        # Move to bottom of stairs
        self.pre_move()
        for p in [(450, 100), (-190, 200)]:
            pos_m = convert_abs_to_monitor(p)
            self.move(pos_m, force_move=True)
        self._pather.traverse_nodes([304], self, timeout=2.5, force_tp=True)
        # Attack to center of stairs
        self._blizzard((-175, -200), spray=30)
        self._ice_blast((30, -60), spray=30)
        wait(0.5)
        self._blizzard((175, -270), spray=30)
        wait(1.0)
        # Move back inside
        self._pather.traverse_nodes_fixed([(1110, 15)], self)
        self._pather.traverse_nodes([300], self, timeout=2.5, force_tp=False)
        # Attack to center
        self._blizzard((-100, 0), spray=10)
        self._ice_blast((-300, 30), spray=50)
        self._blizzard((-175, 50), spray=10)
        wait(1.0)
        # Move back outside and attack
        pos_m = convert_abs_to_monitor((-430, 230))
        self.pre_move()
        self.move(pos_m, force_move=True)
        self._blizzard((-50, -150), spray=30)
        wait(0.5)
        # Move back inside and attack
        pos_m = convert_abs_to_monitor((150, -350))
        self.pre_move()
        self.move(pos_m, force_move=True)
        # Attack sequence center
        self._blizzard((-100, 35), spray=30)
        self._blizzard((-150, 20), spray=30)
        wait(1.0)
        # Move inside
        pos_m = convert_abs_to_monitor((100, -30))
        self.pre_move()
        self.move(pos_m, force_move=True)
        # Attack sequence to center
        self._blizzard((-50, 50), spray=30)
        self._ice_blast((-30, 50), spray=10)
        # Move outside since the trav.py expects to start searching for items there if char can teleport
        self._pather.traverse_nodes([226], self, timeout=2.5, force_tp=True)
        return True

    def kill_nihlathak(self, end_nodes: list[int]) -> bool:
        # Find nilhlatak position
        atk_sequences = max(1, int(Config().char["atk_len_nihlathak"]) - 1)
        for i in range(atk_sequences):
            nihlathak_pos_abs = self._pather.find_abs_node_pos(end_nodes[-1], grab())
            if nihlathak_pos_abs is not None:
                cast_pos_abs = np.array([nihlathak_pos_abs[0] * 1.0, nihlathak_pos_abs[1] * 1.0])
                wait(0.5)
                self._blizzard(cast_pos_abs, spray=0)
                wait(0.2)
                is_nihl = template_finder.search(["NIHL_BAR"], grab(), threshold=0.8, roi=Config().ui_roi["enemy_info"]).valid
                nihl_immune = template_finder.search(["COLD_IMMUNE","COLD_IMMUNES"], grab(), threshold=0.8, roi=Config().ui_roi["enemy_info"]).valid
                if is_nihl:
                    Logger.info("Found him!")
                    if nihl_immune:
                        Logger.info("Cold Immune! - Exiting")
                        return True
        wait(0.5)
        self._cast_static()
        self._blizzard(cast_pos_abs, spray=15)
        # Move to items
        self._pather.traverse_nodes(end_nodes, self, timeout=0.8)
        return True

    def kill_summoner(self) -> bool:
        # Attack
        cast_pos_abs = np.array([0, 0])
        pos_m = convert_abs_to_monitor((-20, 20))
        mouse.move(*pos_m, randomize=80, delay_factor=[0.5, 0.7])
        for _ in range(int(Config().char["atk_len_arc"])):
            self._blizzard(cast_pos_abs, spray=11)
            self._ice_blast(cast_pos_abs, spray=11)
        wait(self._cast_duration, self._cast_duration + 0.2)
        return True

    def _cs_pickit(self, skip_inspect: bool = False):
        new_items = self._pickit.pick_up_items(self)
        self._picked_up_items |= new_items
        #if not skip_inspect and new_items:
        #    set_panel_check_paused(True)
        #    inspect_items(grab(), ignore_sell=True)
        #    set_panel_check_paused(False)

     ########################################################################################
     # Chaos Sanctuary, Trash, Seal Bosses (a = Vizier, b = De Seis, c = Infector) & Diablo #
     ########################################################################################

    def kill_cs_trash(self, location:str) -> bool:

        ###########
        # SEALDANCE
        ###########

        match location:
            case "sealdance": #if seal opening fails & trash needs to be cleared -> used at ANY seal
                self._generic_blizz_attack_sequence()

            ################
            # CLEAR CS TRASH
            ################

            case "rof_01": #node 603 - outside CS in ROF
                if not self._pather.traverse_nodes([603], self): return False #calibrate after static path
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([603], self): return False #calibrate after looting

            case "rof_02": #node 604 - inside ROF
                if not self._pather.traverse_nodes([604], self, timeout=1): return False  #threshold=0.8 (ex 601)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "entrance_hall_01": ##static_path "diablo_entrance_hall_1", node 677, CS Entrance Hall1
                self._pather.traverse_nodes_fixed("diablo_entrance_hall_1", self) # 604 -> 671 Hall1
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "entrance_hall_02":  #node 670,671, CS Entrance Hall1, CS Entrance Hall1
                if not self._pather.traverse_nodes([670], self): return False # pull top mobs 672 to bottom 670
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([671], self): return False # calibrate before static path
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                self._pather.traverse_nodes_fixed("diablo_entrance_hall_2", self) # 671 -> LC Hall2
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            # TRASH LAYOUT A

            case "entrance1_01": #static_path "diablo_entrance_hall_2", Hal1 (before layout check)
                if not self._pather.traverse_nodes([673], self): return False # , timeout=1): # Re-adjust itself and continues to attack
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "entrance1_02": #node 673
                self._pather.traverse_nodes_fixed("diablo_entrance_1_1", self) # Moves char to postion close to node 674 continues to attack
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([674], self): return False#, timeout=1)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "entrance1_03": #node 674
                self._pather.traverse_nodes_fixed("diablo_entrance_1_1", self) #static path to get to be able to spot 676
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([676], self): return False#, timeout=1)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "entrance1_04": #node 676- Hall3
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            # TRASH LAYOUT B

            case "entrance2_01": #static_path "diablo_entrance_hall_2"
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "entrance2_02": #node 682
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "entrance2_03": #node 683
                self._pather.traverse_nodes_fixed("diablo_trash_b_hall2_605_top1", self) #pull mobs from top
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                self._pather.traverse_nodes_fixed("diablo_trash_b_hall2_605_top2", self) #pull mobs from top
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([605], self): return False#, timeout=1)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "entrance2_04": #node 686 - Hall3
                if not self._pather.traverse_nodes([605], self): return False#, timeout=3)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                self._pather.traverse_nodes_fixed("diablo_trash_b_hall2_605_hall3", self)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([609], self): return False#, timeout=1)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                self._pather.traverse_nodes_fixed("diablo_trash_b_hall3_pull_609", self)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([609], self): return False#, timeout=1)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([609], self): return False#, timeout=1)
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            ####################
            # PENT TRASH TO SEAL
            ####################

            case "dia_trash_a" | "dia_trash_b" | "dia_trash_c": #trash before between Pentagramm and Seal A Layoutcheck
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            ###############
            # LAYOUT CHECKS
            ###############

            case "layoutcheck_a" | "layoutcheck_b" | "layoutcheck_c": #layout check seal A, node 619 A1-L, node 620 A2-Y
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            ##################
            # PENT BEFORE SEAL
            ##################

            case "pent_before_a": #node 602, pentagram, before CTA buff & depature to layout check - not needed when trash is skipped & seals run in right order
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "pent_before_b" | "pent_before_c": #node 602, pentagram, before CTA buff & depature to layout check
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            ###########
            # SEAL A1-L
            ###########

            case "A1-L_01":  #node 611 seal layout A1-L: safe_dist
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([610], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([611], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()

            case "A1-L_02":  #node 612 seal layout A1-L: center
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([612], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()

            case "A1-L_03":  #node 613 seal layout A1-L: fake_seal
                if not self._pather.traverse_nodes([613], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "A1-L_seal1":  #node 613 seal layout A1-L: fake_seal
                if not self._pather.traverse_nodes([614], self): return False
                self._generic_blizz_attack_sequence()

            case "A1-L_seal2":  #node 614 seal layout A1-L: boss_seal
                if not self._pather.traverse_nodes([613, 615], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()

            ###########
            # SEAL A2-Y
            ###########

            case "A2-Y_01":  #node 622 seal layout A2-Y: safe_dist
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes_fixed("dia_a2y_hop_622", self): return False
                self._generic_blizz_attack_sequence()
                Logger.debug("A2-Y: Hop!")
                if not self._pather.traverse_nodes([621], self): return False
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([622], self): return False
                self._generic_blizz_attack_sequence()

            case "A2-Y_02":  #node 623 seal layout A2-Y: center
                self._generic_blizz_attack_sequence()

            case "A2-Y_03": #skipped
                self._generic_blizz_attack_sequence()

            case "A2-Y_seal1":  #node 625 seal layout A2-Y: fake seal
                if not self._pather.traverse_nodes([625], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "A2-Y_seal2":
                self._pather.traverse_nodes_fixed("dia_a2y_sealfake_sealboss", self) #instead of traversing node 626 which causes issues
                self._generic_blizz_attack_sequence()
                
            ###########
            # SEAL B1-S
            ###########

            case "B1-S_01" | "B1-S_02" | "B1-S_03":
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "B1-S_seal2": #B only has 1 seal, which is the boss seal = seal2
                if not self._pather.traverse_nodes([634], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            ###########
            # SEAL B2-U
            ###########

            case "B2-U_01" | "B2-U_02" | "B2-U_03":
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "B2-U_seal2": #B only has 1 seal, which is the boss seal = seal2
                self._pather.traverse_nodes_fixed("dia_b2u_bold_seal", self)
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([644], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([648], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([649], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([645], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([644], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()

            ###########
            # SEAL C1-F
            ###########

            case "C1-F_01" | "C1-F_02" | "C1-F_03":
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "C1-F_seal1":
                self._pather.traverse_nodes_fixed("dia_c1f_hop_fakeseal", self)
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([655], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([655], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                
            case "C1-F_seal2":
                self._pather.traverse_nodes_fixed("dia_c1f_654_651", self)
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([652], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([652], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([651], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([652], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            ###########
            # SEAL C2-G
            ###########

            case "C2-G_01" | "C2-G_02" | "C2-G_03": #skipped
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "C2-G_seal1":
                if not self._pather.traverse_nodes([664], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([663, 662], self) or not self._pather.traverse_nodes_fixed("dia_c2g_lc_661", self):
                    return False
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([662], self): return False
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "C2-G_seal2":
                seal_layout="C2-G"
                if not self._pather.traverse_nodes([662], self) or not self._pather.traverse_nodes_fixed("dia_c2g_663", self):
                    return False
                Logger.debug(seal_layout + ": Attacking Infector at position 1/2")
                self._generic_blizz_attack_sequence()
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([663], self): return False # , timeout=1):
                Logger.debug(seal_layout + ": Attacking Infector at position 2/2")
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([664, 665], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case _:
                Logger.error("No location argument given for kill_cs_trash(" + location + "), should not happen")
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                return True


    def kill_vizier(self, seal_layout:str) -> bool:
        match seal_layout:
            case "A1-L":
                if not self._pather.traverse_nodes([612], self): return False # , timeout=1):
                Logger.debug(seal_layout + ": Attacking Vizier at position 1/2")
                self._generic_blizz_attack_sequence()
                Logger.debug(seal_layout + ": Attacking Vizier at position 2/2")
                self._pather.traverse_nodes([611], self, timeout=1)
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([612], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([612], self): return False # , timeout=1): # recalibrate after loot
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "A2-Y":
                if not self._pather.traverse_nodes([627, 622], self): return False # , timeout=1):
                Logger.debug(seal_layout + ": Attacking Vizier at position 1/3")
                self._generic_blizz_attack_sequence()
                Logger.debug(seal_layout + ": Attacking Vizier at position 2/3")
                self._pather.traverse_nodes([623], self, timeout=1)
                self._generic_blizz_attack_sequence()
                Logger.debug(seal_layout + ": Attacking Vizier at position 3/3")
                if not self._pather.traverse_nodes([624], self): return False
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([624], self): return False
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes_fixed("dia_a2y_hop_622", self): return False
                self._generic_blizz_attack_sequence()
                Logger.debug(seal_layout + ": Hop!")
                if not self._pather.traverse_nodes([622], self): return False #, timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([622], self): return False # , timeout=1): #recalibrate after loot
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case _:
                Logger.warning(seal_layout + ": Invalid location for kill_vizier("+ seal_layout +"), should not happen.")
                return False
        return True

    def kill_deseis(self, seal_layout:str) -> bool:
        match seal_layout:
            case "B1-S":
                self._pather.traverse_nodes_fixed("dia_b1s_seal_deseis_foh", self)
                nodes = [631]
                Logger.debug(f"{seal_layout}: Attacking De Seis at position 1/{len(nodes)+1}")
                self._generic_blizz_attack_sequence()
                for i, node in enumerate(nodes):
                    Logger.debug(f"{seal_layout}: Attacking De Seis at position {i+2}/{len(nodes)+1}")
                    self._pather.traverse_nodes([node], self, timeout=1)
                    self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "B2-U":

                self._pather.traverse_nodes_fixed("dia_b2u_644_646", self) # We try to breaking line of sight, sometimes makes De Seis walk into the hammercloud. A better attack sequence here could make sense.
                nodes = [646, 641]
                Logger.debug(seal_layout + ": Attacking De Seis at position 1/{len(nodes)+1}")
                self._generic_blizz_attack_sequence()
                for i, node in enumerate(nodes):
                    Logger.debug(f"{seal_layout}: Attacking De Seis at position {i+2}/{len(nodes)+1}")
                    self._pather.traverse_nodes([node], self, timeout=1)
                    self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([641], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([646], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([646], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                self._cs_pickit()
                if not self._pather.traverse_nodes([640], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([640], self): return False # , timeout=1):
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case _:
                Logger.warning(seal_layout + ": Invalid location for kill_deseis("+ seal_layout +"), should not happen.")
                return False
        return True

    def kill_infector(self, seal_layout:str) -> bool:
        match seal_layout:
            case "C1-F":
                Logger.debug(seal_layout + ": Attacking Infector at position 1/1")
                if not self._pather.traverse_nodes([652], self): return False
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([651], self): return False
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([652], self): return False
                self._generic_blizz_attack_sequence()
                self._pather.traverse_nodes_fixed("dia_c1f_652", self)
                Logger.debug(seal_layout + ": Attacking Infector at position 2/2")
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case "C2-G":
                if not self._pather.traverse_nodes([665], self): return False # , timeout=1):
                Logger.debug(seal_layout + ": Attacking Infector at position 1/2")
                self._generic_blizz_attack_sequence()
                if not self._pather.traverse_nodes([663], self): return False # , timeout=1):
                Logger.debug(seal_layout + ": Attacking Infector at position 2/2")
                self._generic_blizz_attack_sequence()
                self._cs_pickit()

            case _:
                Logger.warning(seal_layout + ": Invalid location for kill_infector("+ seal_layout +"), should not happen.")
                return False
        return True

    def kill_diablo(self) -> bool:
        Logger.debug("Attacking Diablo at position 1/1")
        diablo_abs = [100,-100] #hardcoded dia pos.
        self._blizzard(diablo_abs, spray=5)
        self._cast_static()
        self._ice_blast(diablo_abs, spray=5)
        self._cast_static()
        self._blizzard(diablo_abs, spray=5)
        self._cast_static()
        self._ice_blast(diablo_abs, spray=5)
        self._blizzard(diablo_abs, spray=5)
        self._blizzard(diablo_abs, spray=5)
        wait(3.0)
        self._cs_pickit()
        return True
        
if __name__ == "__main__":
    import os
    import keyboard
    import template_finder
    from pather import Pather
    keyboard.add_hotkey('f12', lambda: Logger.info('Force Exit (f12)') or os._exit(1))
    keyboard.wait("f11")
    from config import Config
    pather = Pather()
    char = BlizzSorc(Config().blizz_sorc, Config().char, pather)
    char.kill_council()
