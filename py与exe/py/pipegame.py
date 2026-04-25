import pygame
import sys
import os
from enum import IntEnum


def resource_path(relative_path):
    """获取资源的绝对路径，用于PyInstaller打包后的资源访问"""
    try:
        # PyInstaller创建的临时文件夹
        base_path = sys._MEIPASS
    except Exception:
        # 正常Python环境
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# 初始化Pygame
pygame.init()

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
BLUE = (30, 144, 255)
GREEN = (50, 205, 50)
RED = (255, 99, 71)
PURPLE = (147, 112, 219)
YELLOW = (255, 215, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# 游戏常量
TILE_SIZE = 116
GRID_OFFSET_X = 100  # 水平方向偏移量增加，为中心化准备
GRID_OFFSET_Y = 50
UI_WIDTH = 300
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60


# 方块类型枚举
class BlockType(IntEnum):
    NORMAL = 0
    ORIGIN = 1
    TERMINAL = 2


# 通道位置枚举
class ChannelPosition(IntEnum):
    NONE = 0
    CENTER = 1
    UPWARDS = 2
    DOWNWARDS = 4
    LEFTWARDS = 8
    RIGHTWARDS = 16


# 方块类
class Block:
    def __init__(self, block_type, channel_position, row, col, static=False, rotation=0):
        self.type = block_type
        self.channel_position = channel_position
        self.row = row
        self.col = col
        self.static = static
        self.rotation = rotation
        self.rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        self.update_position()

    def update_position(self):
        self.rect.x = GRID_OFFSET_X + self.col * TILE_SIZE
        self.rect.y = GRID_OFFSET_Y + self.row * TILE_SIZE

    def move(self, d_row, d_col):
        if not self.static:
            self.row += d_row
            self.col += d_col
            self.update_position()
            return True
        return False


# 关卡类
class Level:
    def __init__(self, level_id, game_id, grid_size, max_moves, data_path):
        self.id = level_id
        self.game_id = game_id
        self.rows, self.cols = grid_size
        self.max_moves = max_moves
        self.data_path = data_path
        self.blocks = []
        self.origin = None
        self.terminal = None
        self.current_moves = 0
        self.move_history = []  # 存储移动历史
        self.parse_data_path()

    def parse_config_str(self, config_str):
        """根据原始Lua代码的ParseConfigStr函数重写解析逻辑"""
        splits = config_str.split('|')
        item_configs = []

        for split in splits:
            subsplits = split.split(':')
            if len(subsplits) < 4:
                continue

            x, y = int(subsplits[0]), int(subsplits[1])
            b_type, b_position = int(subsplits[2]), int(subsplits[3])
            rotation = int(subsplits[4]) if len(subsplits) > 4 else 0

            conf = {}
            conf['row'] = y - 1  # 转换为0索引，y轴从上到下递增
            conf['col'] = x - 1  # 转换为0索引

            # 根据原始代码的解析逻辑
            if b_position == 4 or b_position == 5:
                conf['static'] = True
                if rotation == 1:
                    conf['channel_position'] = ChannelPosition.CENTER | ChannelPosition.UPWARDS
                elif rotation == 2:
                    conf['channel_position'] = ChannelPosition.CENTER | ChannelPosition.RIGHTWARDS
                elif rotation == 3:
                    conf['channel_position'] = ChannelPosition.CENTER | ChannelPosition.DOWNWARDS
                elif rotation == 4:
                    conf['channel_position'] = ChannelPosition.CENTER | ChannelPosition.LEFTWARDS
                else:
                    conf['channel_position'] = ChannelPosition.CENTER | ChannelPosition.DOWNWARDS  # 默认

                conf['type'] = BlockType.ORIGIN if b_position == 4 else BlockType.TERMINAL

            elif b_position == 1:
                conf['type'] = BlockType.NORMAL
                conf['channel_position'] = ChannelPosition.NONE
                conf['static'] = (b_type == 3)

            elif b_position == 2:
                conf['type'] = BlockType.NORMAL
                conf['static'] = (b_type == 3)
                if rotation == 1 or rotation == 3:
                    conf['channel_position'] = ChannelPosition.UPWARDS | ChannelPosition.DOWNWARDS
                elif rotation == 2 or rotation == 4:
                    conf['channel_position'] = ChannelPosition.LEFTWARDS | ChannelPosition.RIGHTWARDS

            elif b_position == 3:
                conf['type'] = BlockType.NORMAL
                conf['static'] = (b_type == 3)
                if rotation == 1:
                    conf['channel_position'] = ChannelPosition.UPWARDS | ChannelPosition.RIGHTWARDS
                elif rotation == 2:
                    conf['channel_position'] = ChannelPosition.RIGHTWARDS | ChannelPosition.DOWNWARDS
                elif rotation == 3:
                    conf['channel_position'] = ChannelPosition.DOWNWARDS | ChannelPosition.LEFTWARDS
                elif rotation == 4:
                    conf['channel_position'] = ChannelPosition.LEFTWARDS | ChannelPosition.UPWARDS

            item_configs.append(conf)

        return item_configs

    def parse_data_path(self):
        """使用新的解析函数"""
        item_configs = self.parse_config_str(self.data_path)

        for conf in item_configs:
            block = Block(
                conf['type'],
                conf.get('channel_position', ChannelPosition.NONE),
                conf['row'],
                conf['col'],
                conf.get('static', False),
                0  # 旋转信息已经包含在channel_position中
            )

            self.blocks.append(block)

            if conf['type'] == BlockType.ORIGIN:
                self.origin = block
            elif conf['type'] == BlockType.TERMINAL:
                self.terminal = block

    def get_block_at(self, row, col):
        """获取指定位置的方块"""
        for block in self.blocks:
            if block.row == row and block.col == col:
                return block
        return None

    def can_move_to(self, block, d_row, d_col):
        """检查方块是否可以移动到目标位置"""
        new_row = block.row + d_row
        new_col = block.col + d_col

        # 检查边界
        if new_row < 0 or new_row >= self.rows or new_col < 0 or new_col >= self.cols:
            return False

        # 检查目标位置是否已有方块
        target_block = self.get_block_at(new_row, new_col)
        return target_block is None

    def move_block(self, block, d_row, d_col):
        """移动方块并记录历史"""
        if not block.static and self.can_move_to(block, d_row, d_col):
            # 记录移动前的状态
            old_row, old_col = block.row, block.col
            block.move(d_row, d_col)
            self.current_moves += 1
            # 记录移动历史
            self.move_history.append({
                'block': block,
                'old_row': old_row,
                'old_col': old_col,
                'new_row': block.row,
                'new_col': block.col
            })
            return True
        return False

    def undo_move(self):
        """回退一步"""
        if self.move_history and self.current_moves > 0:
            last_move = self.move_history.pop()
            block = last_move['block']
            block.row = last_move['old_row']
            block.col = last_move['old_col']
            block.update_position()
            self.current_moves -= 1
            return True
        return False

    def reset(self):
        """重置关卡到初始状态"""
        self.current_moves = 0
        self.move_history = []
        # 重新解析数据路径来重置方块位置
        self.blocks = []
        self.origin = None
        self.terminal = None
        self.parse_data_path()

    def are_blocks_connected(self, block1, block2, direction):
        """检查两个方块是否在指定方向上连接"""
        d_row, d_col = direction

        # 方块1是否向这个方向开口
        block1_open = False
        if d_row == -1:  # 向上
            block1_open = block1.channel_position & ChannelPosition.UPWARDS
        elif d_row == 1:  # 向下
            block1_open = block1.channel_position & ChannelPosition.DOWNWARDS
        elif d_col == -1:  # 向左
            block1_open = block1.channel_position & ChannelPosition.LEFTWARDS
        elif d_col == 1:  # 向右
            block1_open = block1.channel_position & ChannelPosition.RIGHTWARDS

        # 方块2是否向反方向开口
        block2_open = False
        if d_row == -1:  # 方块2需要向下开口
            block2_open = block2.channel_position & ChannelPosition.DOWNWARDS
        elif d_row == 1:  # 方块2需要向上开口
            block2_open = block2.channel_position & ChannelPosition.UPWARDS
        elif d_col == -1:  # 方块2需要向右开口
            block2_open = block2.channel_position & ChannelPosition.RIGHTWARDS
        elif d_col == 1:  # 方块2需要向左开口
            block2_open = block2.channel_position & ChannelPosition.LEFTWARDS

        return block1_open and block2_open

    def check_connection(self):
        """检查起点和终点是否连通（改进版）"""
        if not self.origin or not self.terminal:
            return False

        # 使用改进的DFS检查连通性
        visited = set()

        def dfs(block, from_direction=None):
            """深度优先搜索"""
            if block is None:
                return False

            if block == self.terminal:
                return True

            # 防止循环访问
            if block in visited:
                return False

            visited.add(block)

            # 获取当前方块的所有连接方向
            connections = []
            if block.channel_position & ChannelPosition.UPWARDS:
                connections.append((-1, 0))
            if block.channel_position & ChannelPosition.DOWNWARDS:
                connections.append((1, 0))
            if block.channel_position & ChannelPosition.LEFTWARDS:
                connections.append((0, -1))
            if block.channel_position & ChannelPosition.RIGHTWARDS:
                connections.append((0, 1))

            for d_row, d_col in connections:
                new_row = block.row + d_row
                new_col = block.col + d_col

                # 检查边界
                if 0 <= new_row < self.rows and 0 <= new_col < self.cols:
                    neighbor = self.get_block_at(new_row, new_col)

                    if neighbor:
                        # 检查邻居方块是否有反向连接
                        if self.are_blocks_connected(block, neighbor, (d_row, d_col)):
                            if dfs(neighbor, (d_row, d_col)):
                                return True

            visited.remove(block)
            return False

        return dfs(self.origin)

    def is_complete(self):
        """检查关卡是否完成"""
        return self.check_connection()

    def is_game_over(self):
        """检查是否游戏结束（步数用完）"""
        return self.current_moves >= self.max_moves


# 游戏主类
class PipeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("管道连接小游戏")
        self.clock = pygame.time.Clock()

        # 尝试加载中文字体
        try:
            # 使用resource_path获取字体路径
            font_path = resource_path("fonts/simhei.ttf")
            self.font = pygame.font.Font(font_path, 28)
            self.small_font = pygame.font.Font(font_path, 20)
            self.title_font = pygame.font.Font(font_path, 36)
        except:
            try:
                # 尝试微软雅黑
                font_path = resource_path("fonts/msyh.ttc")
                self.font = pygame.font.Font(font_path, 28)
                self.small_font = pygame.font.Font(font_path, 20)
                self.title_font = pygame.font.Font(font_path, 36)
            except:
                # 如果都失败，使用默认字体
                print("警告：未找到中文字体，将使用默认字体（可能无法显示中文）")
                print("请将中文字体文件放在fonts文件夹中")
                self.font = pygame.font.SysFont(None, 28)
                self.small_font = pygame.font.SysFont(None, 20)
                self.title_font = pygame.font.SysFont(None, 36)

        # 游戏状态
        self.state = "level_select"  # level_select, playing, level_complete, game_over
        self.current_level_index = 0
        self.levels = []
        self.current_level = None
        self.selected_block = None
        self.drag_start_pos = None
        self.game_won = False
        self.show_message = False
        self.message_text = ""
        self.message_type = ""  # "complete" 或 "game_over"

        # 分页相关
        self.current_page = 0
        self.levels_per_page = 20  # 每页显示20个关卡

        # 通关记录
        self.completed_levels = set()  # 记录已通关的关卡索引

        # 加载关卡数据（加载所有60个关卡）
        self.load_levels()

        # 创建关卡选择按钮
        self.level_buttons = []
        self.create_level_buttons()

        # 创建游戏控制按钮
        # 重新调整按钮位置，使用垂直排列
        self.undo_button = pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 160, 100, 40)
        self.reset_button = pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 110, 100, 40)
        self.back_button = pygame.Rect(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 60, 100, 40)

        # 创建消息框按钮（调整位置避免重叠）
        self.message_box_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 200)

        # 为完成消息框设置两个按钮
        self.next_button = pygame.Rect(SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 30, 80, 40)
        self.return_complete_button = pygame.Rect(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 30, 80, 40)

        # 为失败消息框设置两个按钮
        self.restart_button = pygame.Rect(SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 30, 80, 40)
        self.return_fail_button = pygame.Rect(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 30, 80, 40)

        # 创建翻页按钮
        self.prev_button = pygame.Rect(50, SCREEN_HEIGHT - 60, 80, 40)
        self.next_button_page = pygame.Rect(SCREEN_WIDTH - 130, SCREEN_HEIGHT - 60, 80, 40)

    def load_levels(self):
        """加载所有60个关卡数据"""
        # 这里使用所有60个关卡数据
        base_levels = [
            {
                'id': 70076800,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [1],
                'data_path': '1:1:2:3:2|2:1:2:3:3|1:2:2:2:1|1:3:2:4:1|2:3:2:2:1|2:4:3:3:1|3:1:2:1:1|3:2:2:2:1|3:4:1:5:4'
            },
            {
                'id': 70076801,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [2],
                'data_path': '1:1:2:3:2|1:2:3:3:1|1:3:2:1:1|2:1:2:2:2|2:3:2:2:2|3:1:2:2:2|3:3:1:5:1|3:4:2:1:1|4:1:3:4:4|4:2:2:3:3|4:4:2:1:1|4:3:2:2:2'
            },
            {
                'id': 70076802,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [4],
                'data_path': '1:1:3:4:2|1:4:1:5:2|2:2:2:2:2|2:4:3:2:2|3:1:2:2:2|3:2:2:1:1|3:3:2:2:1|3:4:2:2:2|4:1:3:3:3|4:3:3:2:1|4:4:3:3:4'
            },
            {
                'id': 70076803,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [8],
                'data_path': '1:2:3:2:1|1:3:1:5:1|2:2:2:3:2|2:3:2:1:1|3:1:2:3:1|3:2:3:2:2|3:3:3:4:2|3:4:2:3:1|4:1:2:3:3|4:2:2:3:3|4:3:3:3:4|4:4:2:1:1'
            },
            {
                'id': 70076804,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [7],
                'data_path': '1:2:2:2:1|1:3:1:5:1|1:4:2:1:1|2:1:2:3:2|2:2:2:3:1|2:3:2:2:2|3:2:2:3:3|3:3:2:1:1|4:1:3:4:3|4:2:2:3:4|4:3:2:3:3|4:4:2:1:1'
            },
            {
                'id': 70076805,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [5],
                'data_path': '1:1:2:1:1|1:2:3:3:2|1:3:2:2:1|1:4:1:5:1|2:1:2:3:3|2:4:2:1:1|3:1:2:3:2|3:2:2:3:4|3:3:2:3:1|3:4:2:1:1|4:1:2:3:2|4:2:3:4:4|4:3:2:1:1|4:4:2:1:1'
            },
            {
                'id': 70076806,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [6],
                'data_path': '1:1:2:3:1|1:3:1:5:2|2:1:2:3:2|2:2:3:4:4|2:3:2:2:2|2:4:2:1:1|3:1:2:2:2|3:2:2:3:3|3:3:2:3:4|3:4:2:1:1|4:1:2:1:1|4:2:2:2:1|4:3:2:1:1|4:4:2:2:1'
            },
            {
                'id': 70076807,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [10],
                'data_path': '1:1:2:3:2|1:2:2:2:1|1:3:2:1:1|2:1:2:1:1|2:3:1:5:1|2:4:2:1:1|3:1:2:3:3|3:2:2:3:1|3:4:3:4:2|4:1:2:2:1|4:2:2:2:1|4:3:3:3:3|4:4:3:3:4'
            },
            {
                'id': 70076808,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [6],
                'data_path': '1:1:3:3:2|1:2:3:2:1|1:3:2:2:1|1:4:3:4:1|2:1:3:3:3|2:2:3:3:1|2:4:2:1:1|3:1:2:1:1|3:2:2:3:3|3:3:2:1:1|3:4:2:2:2|4:2:2:2:1|4:4:1:5:1'
            },
            {
                'id': 70076809,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [5],
                'data_path': '1:1:2:1:1|1:2:2:1:1|1:3:2:2:2|1:4:1:5:2|2:1:3:3:2|2:2:2:3:3|2:3:2:3:1|2:4:3:2:2|3:1:3:4:4|3:3:2:3:4|4:1:2:1:1|4:2:2:1:1|4:3:2:2:1|4:4:2:3:2'
            },
            {
                'id': 70076810,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [10],
                'data_path': '1:1:2:2:2|1:3:2:2:1|1:4:3:4:1|2:1:2:3:2|2:2:2:1:1|2:3:2:3:3|2:4:2:3:1|3:1:2:2:2|3:3:3:3:2|4:1:2:3:3|4:3:3:3:4|4:4:1:5:4'
            },
            {
                'id': 70076811,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [7],
                'data_path': '1:1:2:1:1|1:2:2:3:2|2:1:2:2:1|2:2:2:2:2|2:3:2:3:1|3:1:3:3:2|3:2:3:3:1|3:3:2:2:2|4:1:3:4:4|4:2:3:3:3|4:3:3:3:4|4:4:1:5:4'
            },
            {
                'id': 70076812,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [7],
                'data_path': '1:1:3:3:2|1:2:2:3:1|1:4:2:2:2|2:1:2:2:2|2:2:2:2:1|2:3:2:1:1|2:4:2:1:1|3:1:3:2:2|3:3:2:2:2|3:4:2:3:1|4:1:3:4:4|4:2:2:3:3|4:3:1:5:3|4:4:2:3:4'
            },
            {
                'id': 70076813,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [6],
                'data_path': '1:2:3:4:2|1:3:2:3:2|1:4:2:3:1|2:1:2:1:1|2:3:2:3:2|2:4:2:3:1|3:1:2:3:2|3:2:2:3:4|3:4:1:5:4|4:1:2:3:3|4:2:2:2:2|4:3:2:2:1|4:4:2:3:4'
            },
            {
                'id': 70076814,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [5],
                'data_path': '1:1:2:3:2|1:2:3:3:2|1:3:1:5:1|1:4:2:2:1|2:1:2:2:2|2:3:2:3:4|3:1:2:1:1|3:3:3:4:3|3:4:3:3:1|4:1:2:3:3|4:2:2:2:1|4:3:2:2:1|4:4:3:3:4'
            },
            {
                'id': 70076815,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [8],
                'data_path': '1:1:2:3:2|1:4:2:2:2|2:1:2:3:2|2:2:3:3:4|2:3:2:3:1|3:1:3:4:4|3:4:1:5:2|4:1:2:1:1|4:2:2:3:3|4:3:2:2:2|4:4:3:3:4'
            },
            {
                'id': 70076816,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [12],
                'data_path': '1:2:3:4:2|1:3:2:1:1|1:4:2:2:1|2:1:3:3:2|2:2:3:3:4|2:3:2:2:1|2:4:1:5:2|3:1:2:3:3|3:2:2:2:1|3:3:2:3:4|3:4:3:2:2|4:2:2:2:2'
            },
            {
                'id': 70076817,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [6],
                'data_path': '1:2:2:2:1|1:3:3:4:3|2:1:2:2:1|2:3:2:3:2|2:4:2:3:1|3:1:1:5:2|3:4:2:3:4|4:1:2:3:3|4:2:3:2:1|4:3:2:2:2|4:4:2:3:4'
            },
            {
                'id': 70076818,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [9],
                'data_path': '1:1:2:3:2|1:2:2:3:2|1:4:3:4:1|2:1:2:2:2|2:2:3:3:4|2:3:2:2:1|2:4:2:2:1|3:4:1:5:1|4:1:3:3:3|4:2:2:3:2|4:3:2:3:4|4:4:2:1:1'
            },
            {
                'id': 70076819,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [7],
                'data_path': '1:1:2:3:2|1:3:2:2:1|1:4:2:3:1|2:1:3:4:3|2:4:2:3:4|3:1:2:1:1|3:3:3:3:2|3:4:2:2:2|4:1:2:1:1|4:2:1:5:3|4:3:2:3:4|4:4:2:3:4'
            },
            {
                'id': 70076820,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [11],
                'data_path': '1:1:2:2:1|1:3:2:2:1|1:4:2:3:1|1:5:2:2:2|2:1:2:3:2|2:2:2:3:3|2:3:2:2:1|2:4:3:4:1|2:5:2:3:1|3:1:3:2:2|3:2:2:2:1|3:5:2:2:1|4:1:2:3:2|4:2:2:2:1|4:4:2:2:1|4:5:2:3:4|5:1:2:3:3|5:2:2:2:1|5:3:1:5:1|5:5:2:3:4'
            },
            {
                'id': 70076821,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [13],
                'data_path': '1:1:1:5:3|1:2:3:2:1|1:3:2:2:1|1:4:2:1:1|1:5:2:2:1|2:3:2:3:2|2:4:2:1:1|2:5:2:3:1|3:2:2:2:2|3:3:2:3:1|3:4:2:2:2|4:1:3:4:2|4:2:2:2:2|4:3:2:2:2|4:4:2:3:4|4:5:2:2:2|5:1:3:3:3|5:2:3:3:4|5:3:2:3:3|5:4:2:2:1'
            },
            {
                'id': 70076822,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [10],
                'data_path': '1:1:3:3:2|1:3:2:3:1|1:4:2:2:1|1:5:3:4:2|2:1:3:2:2|2:2:2:2:1|2:3:2:2:1|2:4:2:2:1|2:5:2:3:4|3:1:3:3:3|3:3:2:3:3|3:4:2:2:1|3:5:2:3:1|4:1:1:5:3|4:2:3:2:1|4:3:2:3:4|4:4:2:3:1|4:5:2:3:4|5:3:2:2:1|5:4:2:1:1|5:5:2:1:1'
            },
            {
                'id': 70076823,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [10],
                'data_path': '1:1:2:2:2|1:2:2:3:2|1:3:1:5:2|1:4:2:1:1|2:1:2:3:3|2:2:2:3:1|2:3:2:3:3|2:4:2:3:4|3:1:2:3:1|3:3:2:3:4|3:4:2:3:1|4:1:3:4:3|4:2:2:3:4'
            },
            {
                'id': 70076824,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [15],
                'data_path': '1:2:3:4:2|1:3:2:3:2|1:4:2:3:4|1:5:2:3:1|2:2:3:2:2|2:3:1:5:3|2:4:2:2:2|2:5:2:2:2|3:2:2:2:2|3:3:2:2:1|3:5:2:2:2|4:2:2:2:1|4:3:2:3:2|4:4:2:2:2|4:5:2:2:1|5:2:2:3:3|5:3:2:3:4|5:4:2:2:1|5:5:2:3:4'
            },
            {
                'id': 70076825,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [10],
                'data_path': '1:1:2:3:2|1:2:2:2:1|1:3:2:3:1|2:1:2:3:3|2:2:2:2:1|2:3:2:3:1|2:4:3:4:4|3:1:1:5:3|3:2:2:2:1|3:4:2:2:2|4:2:2:3:1|4:3:2:3:3|4:4:2:3:4'
            },
            {
                'id': 70076826,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [15],
                'data_path': '1:1:2:3:2|1:4:2:3:1|1:5:3:3:1|2:1:3:2:2|2:2:3:4:3|2:3:2:2:1|2:4:2:2:1|2:5:3:2:2|3:1:3:2:2|3:2:2:2:1|3:3:2:2:1|3:4:2:2:2|3:5:1:5:4|4:1:3:2:2|4:2:2:2:1|4:3:2:3:4|4:4:2:3:2|5:1:2:3:3|5:3:2:3:4'
            },
            {
                'id': 70076827,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [11],
                'data_path': '1:2:3:3:2|1:3:1:5:1|1:4:3:4:2|2:1:2:3:2|2:2:2:3:4|2:3:2:2:2|2:4:2:3:2|3:1:2:3:3|3:2:2:3:4|4:1:2:2:1|4:2:2:2:2|4:3:2:3:4|4:4:2:2:1'
            },
            {
                'id': 70076828,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [8],
                'data_path': '1:1:3:4:2|1:2:2:3:2|1:3:2:2:1|1:4:2:3:1|1:5:2:2:1|2:1:3:2:2|2:2:3:3:3|2:3:1:5:1|2:5:2:2:2|3:1:3:2:2|3:2:2:3:2|3:5:2:3:4|4:1:3:2:2|4:2:2:2:1|4:3:2:2:1|4:5:2:2:1|5:1:2:3:3|5:2:2:2:2|5:3:2:3:4|5:5:2:2:1'
            },
            {
                'id': 70076829,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [13],
                'data_path': '1:3:2:2:1|1:4:2:3:1|1:5:2:3:4|2:1:1:5:3|2:2:3:2:1|2:3:2:3:2|2:5:2:3:4|3:3:2:2:2|3:4:2:3:2|3:5:2:2:1|4:1:3:4:3|4:2:3:3:1|4:3:2:2:2|4:4:2:3:4|4:5:2:3:2|5:2:3:3:3|5:4:2:2:1|5:5:2:1:1'
            },
            {
                'id': 70076830,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [15],
                'data_path': '1:2:2:3:2|1:3:2:3:4|1:4:2:3:1|2:1:2:2:2|2:2:3:4:4|2:4:2:3:1|3:1:1:5:3|3:2:2:3:3|3:4:2:2:1|4:1:2:2:2|4:2:2:3:3|4:4:2:2:1'
            },
            {
                'id': 70076831,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [12],
                'data_path': '1:1:2:2:2|1:2:2:3:1|1:3:2:2:2|1:4:3:2:1|2:1:2:3:2|2:4:2:2:2|2:5:2:3:1|3:1:1:5:4|3:2:2:2:1|3:3:2:2:1|3:4:2:3:1|3:5:2:2:1|4:1:2:3:4|4:2:3:4:3|4:3:3:2:1|4:4:2:2:1|4:5:3:3:4|5:1:2:3:3|5:2:2:1:1|5:3:2:1:1|5:5:2:1:1'
            },
            {
                'id': 70076832,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [15],
                'data_path': '1:1:2:3:2|1:2:2:3:3|1:4:2:1:1|2:1:2:2:1|2:2:2:2:2|2:4:1:5:1|3:1:2:2:1|3:2:2:2:1|3:3:2:2:1|3:4:2:2:2|4:1:2:1:1|4:3:2:3:2|4:4:3:4:1'
            },
            {
                'id': 70076833,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [14],
                'data_path': '1:1:1:5:2|1:2:2:2:2|1:3:3:4:3|2:2:2:3:4|2:3:2:2:2|2:4:2:3:1|3:1:2:3:3|3:2:3:3:1|3:3:2:3:4|3:4:2:2:1|4:1:2:2:2|4:3:2:3:3|4:4:2:2:2'
            },
            {
                'id': 70076834,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [12],
                'data_path': '1:1:3:4:3|1:3:2:3:1|1:4:2:3:1|2:1:2:3:4|2:2:2:3:2|2:4:2:2:2|3:2:2:2:1|3:3:1:5:3|3:4:2:3:4|4:1:2:2:2|4:3:2:3:3|4:4:2:2:1'
            },
            {
                'id': 70076835,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [20],
                'data_path': '1:2:3:2:1|1:3:2:2:2|1:4:2:2:1|1:5:2:2:2|2:1:2:3:2|2:2:2:2:2|2:5:2:2:1|3:1:2:3:1|3:2:2:2:2|3:3:2:1:1|3:4:2:3:2|3:5:2:3:1|4:1:1:5:4|4:2:2:3:1|4:3:2:3:4|4:4:3:4:4|5:1:2:3:1|5:2:2:1:1|5:3:2:3:4|5:4:2:3:3|5:5:2:1:1'
            },
            {
                'id': 70076836,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [11],
                'data_path': '1:1:3:3:2|1:3:2:3:1|1:4:1:5:1|2:1:2:3:4|2:2:2:2:1|2:3:2:3:2|3:1:2:2:1|3:3:2:2:1|3:4:3:4:4|4:1:2:3:4|4:2:2:2:2|4:3:2:3:3|4:4:2:2:2'
            },
            {
                'id': 70076837,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [12],
                'data_path': '1:1:2:3:2|1:2:2:3:4|1:3:2:2:1|1:4:3:4:1|2:1:2:3:2|2:2:2:3:4|2:4:2:1:1|3:2:2:3:2|4:1:3:3:3|4:2:2:2:1|4:3:1:5:1|4:4:2:2:1'
            },
            {
                'id': 70076838,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [18],
                'data_path': '1:1:2:2:2|1:2:2:2:2|1:3:2:2:2|1:4:2:3:3|2:2:2:3:1|2:3:2:3:2|2:4:2:2:1|3:2:2:1:1|3:3:2:2:1|3:4:1:5:4|4:1:3:4:4|4:2:2:1:1|4:3:2:2:1|4:4:2:1:1'
            },
            {
                'id': 70076839,
                'game_id': 70441032,
                'grid': [4, 4],
                'site': [14],
                'data_path': '1:1:2:3:2|1:2:2:2:2|1:3:2:3:2|1:4:2:3:1|2:1:2:3:4|2:2:2:3:3|2:3:2:2:2|3:2:2:2:1|3:3:2:3:2|3:4:1:5:4|4:1:3:4:4|4:2:2:3:4|4:3:2:3:1|4:4:2:3:3'
            },
            {
                'id': 70076840,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [11],
                'data_path': '1:1:1:5:2|1:3:2:3:2|1:4:2:2:1|1:6:2:2:1|2:2:2:2:2|2:4:2:2:1|3:1:2:2:2|3:3:2:2:1|3:5:2:3:2|3:6:2:3:1|4:3:3:4:1|4:4:2:3:1|5:1:2:2:2|5:2:2:2:2|5:3:2:2:1|5:4:2:2:2|5:5:2:2:1|5:6:2:2:2|6:1:3:3:3|6:5:2:3:3|6:6:2:3:4'
            },
            {
                'id': 70076841,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [12],
                'data_path': '1:1:2:3:2|1:3:2:2:1|1:4:2:3:1|1:5:3:4:2|1:6:2:2:1|2:1:2:2:2|2:3:2:2:1|2:5:2:2:2|3:1:2:3:4|3:2:2:1:1|3:3:2:2:2|3:4:2:2:2|3:5:2:2:2|3:6:2:2:2|4:1:2:2:2|4:2:2:2:2|4:3:2:3:1|4:4:2:2:2|4:5:2:2:2|4:6:2:2:1|5:1:1:5:4|5:4:2:3:3|5:5:2:1:1|6:2:2:3:2|6:3:2:1:1|6:4:2:3:3|6:5:2:2:2|6:6:2:3:4'
            },
            {
                'id': 70076842,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [9],
                'data_path': '1:1:2:1:1|1:2:3:4:2|1:3:2:3:2|1:4:2:3:4|1:5:2:3:1|2:1:2:3:1|2:2:2:3:3|2:3:2:1:1|2:4:2:2:2|2:5:2:2:2|3:3:2:1:1|3:4:2:2:1|3:5:2:2:1|4:1:2:2:1|4:2:2:2:2|4:4:2:3:1|4:5:1:5:4|5:3:2:2:2|5:5:2:3:2'
            },
            {
                'id': 70076843,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [9],
                'data_path': '1:1:2:1:1|1:2:2:2:1|1:4:2:3:1|1:5:2:2:1|2:1:1:5:3|2:2:2:2:1|2:3:2:2:1|2:4:2:2:2|2:5:2:2:2|3:1:2:1:1|3:2:3:4:3|3:3:2:3:1|3:4:2:1:1|4:1:2:1:1|4:4:2:3:1|4:5:2:2:2|5:1:2:3:2|5:3:2:2:2|5:4:2:3:3|5:5:2:3:4'
            },
            {
                'id': 70076844,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [13],
                'data_path': '1:1:2:3:2|1:2:2:2:1|1:3:2:3:1|1:4:2:2:1|1:5:2:2:1|1:6:3:4:1|2:1:2:3:4|2:4:2:2:1|2:6:2:2:2|3:1:2:2:2|3:2:2:2:2|3:3:2:2:1|3:5:2:2:1|3:6:2:2:2|4:1:2:3:3|4:2:2:2:1|4:4:2:2:2|4:5:2:2:1|4:6:2:3:1|5:1:1:5:3|5:3:2:2:1|5:4:2:2:2|5:6:2:3:4|6:2:2:2:1|6:3:2:2:1|6:5:2:2:1'
            },
            {
                'id': 70076845,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [11],
                'data_path': '1:2:2:3:2|1:3:2:2:1|1:4:2:2:1|1:5:2:1:1|1:6:2:3:1|2:1:3:4:2|2:3:2:3:2|2:5:2:2:1:|2:6:1:5:4|3:1:2:2:2|3:2:2:2:2|3:4:2:2:2|3:5:2:2:1|3:6:2:1:1|4:1:2:2:2|4:2:2:2:2|4:3:2:2:2|4:4:2:3:2|4:6:2:3:1|5:2:2:3:4|5:4:2:3:1|5:6:2:1:1|6:1:2:2:2|6:2:2:3:3|6:3:2:2:1|6:4:2:1:1|6:5:2:2:2|6:6:2:1:1'
            },
            {
                'id': 70076846,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [11],
                'data_path': '1:1:2:2:2|1:2:2:3:2|1:4:2:2:1|1:5:2:3:1|2:1:2:2:2|2:2:2:2:1|2:4:2:3:3|2:5:2:2:1|3:2:3:4:3|3:3:2:2:1|3:4:2:3:4|3:5:2:2:2|4:1:2:3:3|4:2:2:2:1|4:4:1:5:1|4:5:2:3:4|5:1:2:3:2|5:2:2:2:1|5:3:2:2:2|5:5:2:3:1'
            },
            {
                'id': 70076847,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [10],
                'data_path': '1:1:2:2:2|1:2:2:1:1|1:3:2:3:3|1:4:2:1:1|1:5:2:2:1|1:6:3:4:2|2:1:2:1:1|2:2:2:2:1|2:4:2:3:4|2:5:2:1:1|2:6:2:2:2|3:2:2:3:2|3:3:2:2:1|3:4:2:2:2|3:5:2:3:1|4:1:2:3:1|4:2:2:3:2|4:4:2:2:2|4:5:2:2:1|5:2:2:2:2|5:5:2:2:2|6:2:1:5:4|6:3:2:2:1|6:4:2:3:3|6:5:2:2:2|6:6:2:3:4'
            },
            {
                'id': 70076848,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [13],
                'data_path': '1:2:2:3:1|1:3:2:3:2|1:4:2:2:1|1:5:2:3:1|1:6:2:2:2|2:3:1:5:4|2:5:2:3:2|2:6:2:2:1|3:5:2:3:1|3:6:2:2:2|3:4:2:2:1|4:2:2:3:2|4:3:2:3:1|4:4:2:2:1|4:5:2:1:1|4:6:2:3:4|5:1:2:2:2|5:2:2:2:1|5:3:2:2:1|5:5:2:3:3|5:6:2:2:2|6:1:3:4:4|6:2:2:2:1|6:3:2:1:1|6:4:2:3:4|6:5:2:2:1|6:6:2:1:1'
            },
            {
                'id': 70076849,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [10],
                'data_path': '1:1:1:5:2|1:2:2:3:2|1:3:2:2:1|1:4:2:3:1|1:5:2:2:2|2:1:2:2:2|2:2:2:2:2|2:4:2:3:2|2:5:2:2:1|3:1:2:2:2|3:4:2:3:1|3:5:3:4:4|4:1:2:2:1|4:2:2:3:3|4:3:2:2:2|4:4:2:3:2|4:5:2:1:1|5:2:2:3:4|5:3:2:3:1|5:5:2:2:2'
            },
            {
                'id': 70076850,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [15],
                'data_path': '1:3:2:3:1|1:4:2:2:2|2:1:2:3:2|2:3:2:3:1|2:4:2:2:2|2:5:2:2:2|3:2:2:2:2|3:4:2:2:2|3:5:1:5:3|3:6:2:3:1|4:1:2:3:1|4:2:2:2:2|4:4:2:2:1|4:5:2:2:2|4:6:2:2:2|5:2:3:4:4|5:3:2:1:1|5:4:2:1:1|5:6:2:2:1|6:2:2:3:3|6:3:2:2:1|6:4:2:1:1|6:5:2:2:1|6:6:2:3:4'
            },
            {
                'id': 70076851,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [11],
                'data_path': '1:1:2:1:1|1:2:2:1:1|1:3:2:2:1|1:4:2:1:1|1:5:2:2:1|2:1:1:5:2|2:3:2:3:1|2:5:2:2:2|3:1:2:2:2|3:2:2:3:1|3:3:2:2:1|3:5:2:3:2|4:1:2:3:3|4:2:2:3:2|4:3:2:3:1|4:4:2:2:1|4:5:2:3:4|5:1:2:3:2|5:3:3:4:3|5:4:2:2:1|5:5:2:3:4'
            },
            {
                'id': 70076852,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [10],
                'data_path': '1:1:2:3:2|1:2:2:2:1|1:3:3:4:1|1:4:2:3:2|1:6:2:3:1|2:2:2:2:2|2:3:2:3:2|2:4:2:2:2|2:6:2:2:2|3:3:2:2:1|3:4:1:5:1|3:5:2:2:1|3:6:2:3:2|4:2:2:2:2|4:3:2:2:2|4:4:2:3:1|4:5:2:1:1|4:6:2:1:1|5:1:2:3:4|5:2:2:2:2|5:5:2:3:3|5:6:2:2:1|6:1:2:2:2|6:2:2:3:3|6:3:2:2:2|6:4:2:1:1|6:5:2:3:2'
            },
            {
                'id': 70076853,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [14],
                'data_path': '1:1:2:3:2|1:2:2:3:2|1:3:2:2:1|1:4:3:4:1|1:5:2:1:1|1:6:2:1:1|2:1:2:2:2|2:3:2:2:2|2:4:2:2:1|2:5:2:2:2|3:1:2:2:1|3:4:2:3:1|3:6:2:2:2|4:1:2:2:2|4:2:1:5:3|4:3:2:2:1|4:4:2:2:1|4:6:2:2:2|5:1:2:3:3|5:2:2:1:1|5:3:2:2:1|5:4:2:2:2|5:5:2:2:1|5:6:2:1:1|6:1:2:2:1|6:2:2:2:1|6:3:2:2:1|6:5:2:3:4|6:6:2:1:1'
            },
            {
                'id': 70076854,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [12],
                'data_path': '1:1:3:4:2|1:2:2:3:2|1:4:2:3:1|1:5:2:2:2|1:6:2:3:1|2:1:2:2:2|2:2:2:2:2|2:3:2:2:2|2:4:2:3:2|2:5:2:2:2|3:2:2:2:2|3:3:2:2:2|3:4:1:5:4|3:5:2:2:2|4:3:2:3:3|4:4:2:2:2|4:5:2:2:1|4:6:2:2:2|5:2:2:2:2|5:3:2:2:1|5:6:2:2:2|6:1:2:3:3|6:2:2:2:2|6:4:2:2:1|6:5:2:3:4|6:6:2:3:4'
            },
            {
                'id': 70076855,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [17],
                'data_path': '1:2:2:3:2|1:3:2:2:1|1:5:2:3:1|2:1:2:2:2|2:2:2:2:1|2:3:3:4:2|2:4:2:1:1|2:5:2:2:1|2:6:2:1:1|3:1:2:2:2|3:3:2:2:2|3:4:2:2:2|3:5:2:3:2|3:6:2:1:1|4:1:2:2:2|4:2:2:3:3|4:3:2:1:1|4:4:2:2:1|4:5:2:2:2|5:1:1:5:4|5:2:2:2:2|5:3:2:3:1|5:4:2:2:1|5:5:2:3:4|5:6:2:1:1|6:2:2:2:1|6:3:2:1:1|6:4:2:2:2|6:5:2:1:1'
            },
            {
                'id': 70076856,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [16],
                'data_path': '1:1:2:3:2|1:3:2:2:1|1:4:2:2:1|1:5:2:3:1|2:1:2:3:2|2:2:2:2:1|2:3:2:2:1|2:4:2:2:2|2:5:2:2:2|3:1:2:2:2|3:2:2:2:2|3:3:2:2:1|3:5:2:2:1|4:1:2:3:3|4:2:2:3:1|4:3:2:2:1|4:4:3:4:1|4:5:2:2:2|5:1:1:5:3|5:2:2:2:1|5:3:2:2:1|5:5:2:3:4'
            },
            {
                'id': 70076857,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [10],
                'data_path': '1:2:2:3:1|1:2:2:2:2|1:3:3:4:2|1:4:2:3:1|2:2:2:1:1|2:3:2:2:2|2:5:1:5:2|3:2:2:2:1|3:3:2:3:4|3:5:2:2:2|4:1:2:3:1|4:2:2:3:2|4:3:2:2:1|4:4:2:3:1|4:5:2:2:2|5:1:2:2:1|5:2:2:3:3|5:3:2:2:1|5:4:2:3:4|5:5:2:2:2'
            },
            {
                'id': 70076858,
                'game_id': 70441032,
                'grid': [6, 6],
                'site': [11],
                'data_path': '1:1:2:3:2|1:2:2:1:1|1:3:2:2:1|1:4:2:3:4|1:5:2:2:1|2:2:2:1:1|2:3:2:2:1|2:4:2:3:1|3:1:2:2:2|3:2:2:3:3|3:3:2:1:1|3:4:3:4:4|3:6:2:2:1|4:1:2:3:2|4:3:2:2:1|4:4:2:1:1|4:5:1:5:2|4:6:2:1:1|5:1:2:2:2|5:2:2:2:1|5:4:2:2:1|5:5:2:3:4|5:6:2:2:1|6:1:2:3:3|6:2:2:1:1|6:3:2:3:1|6:4:2:1:1|6:5:2:1:1|6:6:2:2:2'
            },
            {
                'id': 70076859,
                'game_id': 70441032,
                'grid': [5, 5],
                'site': [16],
                'data_path': '1:1:2:3:2|1:2:2:3:2|1:4:2:2:1|1:5:2:2:1|2:1:2:1:1|2:2:2:2:2|2:3:2:2:2|2:4:2:1:1|2:5:2:3:1|3:1:2:3:2|3:2:2:3:3|3:3:1:5:1|3:5:2:2:1|4:1:3:4:3|4:2:2:1:1|4:4:2:2:1|4:5:2:2:2|5:2:2:3:1|5:3:2:2:1|5:4:2:3:1|5:5:2:3:4'
            }
        ]

        # 这里使用你提供的完整60个关卡数据
        # 由于代码长度限制，这里只显示部分关卡，实际代码应包含完整60个关卡
        full_levels_data = [
            {'id': 70076800, 'game_id': 70441032, 'grid': [4, 4], 'site': [1],
             'data_path': '1:1:2:3:2|2:1:2:3:3|1:2:2:2:1|1:3:2:4:1|2:3:2:2:1|2:4:3:3:1|3:1:2:1:1|3:2:2:2:1|3:4:1:5:4'},
            # ... 其他59个关卡数据
        ]

        # 使用你提供的完整60个关卡数据
        for level_data in base_levels:
            level = Level(
                level_data['id'],
                level_data['game_id'],
                level_data['grid'],
                level_data['site'][0],
                level_data['data_path']
            )
            self.levels.append(level)

    def create_level_buttons(self):
        """创建当前页的关卡选择按钮"""
        self.level_buttons = []
        start_index = self.current_page * self.levels_per_page
        end_index = min(start_index + self.levels_per_page, len(self.levels))

        for i in range(start_index, end_index):
            relative_index = i - start_index
            row = relative_index // 5  # 每行5个按钮
            col = relative_index % 5
            x = 150 + col * 120
            y = 150 + row * 60
            button = pygame.Rect(x, y, 100, 40)
            self.level_buttons.append((button, i))

    def start_level(self, level_index):
        """开始指定关卡"""
        if 0 <= level_index < len(self.levels):
            self.current_level_index = level_index
            self.current_level = self.levels[level_index]
            self.current_level.reset()
            self.selected_block = None
            self.drag_start_pos = None
            self.game_won = False
            self.show_message = False
            self.state = "playing"

    def show_complete_message(self):
        """显示关卡完成消息"""
        self.show_message = True
        self.message_text = f"恭喜！\n你通过了第{self.current_level_index + 1}关！"
        self.message_type = "complete"
        # 记录通关
        self.completed_levels.add(self.current_level_index)

    def show_game_over_message(self):
        """显示游戏结束消息"""
        self.show_message = True
        self.message_text = f"步数已用完！\n你未能通过第{self.current_level_index + 1}关。"
        self.message_type = "game_over"

    def next_level(self):
        """进入下一关"""
        if self.current_level_index + 1 < len(self.levels):
            self.start_level(self.current_level_index + 1)
        else:
            self.state = "level_select"
            self.show_message = False

    def handle_message_box_events(self, event):
        """处理消息框事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()

            if self.message_type == "complete":
                # 关卡完成消息框
                if self.next_button.collidepoint(pos) and self.current_level_index + 1 < len(self.levels):
                    self.next_level()
                elif self.return_complete_button.collidepoint(pos):
                    self.state = "level_select"
                    self.show_message = False

            elif self.message_type == "game_over":
                # 游戏结束消息框
                if self.restart_button.collidepoint(pos):
                    self.current_level.reset()
                    self.game_won = False
                    self.show_message = False
                elif self.return_fail_button.collidepoint(pos):
                    self.state = "level_select"
                    self.show_message = False

    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # 如果有消息框显示，优先处理消息框事件
            if self.show_message:
                self.handle_message_box_events(event)
                continue

            if self.state == "level_select":
                # 关卡选择界面
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    for button, level_index in self.level_buttons:
                        if button.collidepoint(pos):
                            self.start_level(level_index)
                            break

                    # 翻页按钮
                    if self.current_page > 0 and self.prev_button.collidepoint(pos):
                        self.current_page -= 1
                        self.create_level_buttons()
                    elif (self.current_page + 1) * self.levels_per_page < len(
                            self.levels) and self.next_button_page.collidepoint(pos):
                        self.current_page += 1
                        self.create_level_buttons()

            elif self.state == "playing":
                # 游戏界面
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()

                    # 检查是否点击了方块
                    for block in self.current_level.blocks:
                        if block.rect.collidepoint(pos) and not block.static:
                            self.selected_block = block
                            self.drag_start_pos = pos
                            break

                    # 检查是否点击了回退按钮
                    if self.undo_button.collidepoint(pos):
                        self.current_level.undo_move()
                        self.selected_block = None
                        self.game_won = False

                    # 检查是否点击了重置按钮
                    if self.reset_button.collidepoint(pos):
                        self.current_level.reset()
                        self.selected_block = None
                        self.game_won = False

                    # 检查是否点击了返回按钮
                    if self.back_button.collidepoint(pos):
                        self.state = "level_select"
                        self.selected_block = None

                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.selected_block and self.drag_start_pos:
                        # 计算拖动方向和距离
                        end_pos = pygame.mouse.get_pos()
                        dx = end_pos[0] - self.drag_start_pos[0]
                        dy = end_pos[1] - self.drag_start_pos[1]

                        # 判断主要拖动方向
                        if abs(dx) > abs(dy) and abs(dx) > 20:  # 水平拖动
                            d_col = 1 if dx > 0 else -1
                            self.current_level.move_block(self.selected_block, 0, d_col)
                        elif abs(dy) > 20:  # 垂直拖动
                            d_row = 1 if dy > 0 else -1
                            self.current_level.move_block(self.selected_block, d_row, 0)

                        self.selected_block = None
                        self.drag_start_pos = None

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # 按R重置关卡
                        self.current_level.reset()
                        self.selected_block = None
                        self.game_won = False
                    elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:  # 按Ctrl+Z回退
                        self.current_level.undo_move()
                        self.selected_block = None
                        self.game_won = False
                    elif event.key == pygame.K_ESCAPE:  # 按ESC返回关卡选择
                        self.state = "level_select"
                        self.selected_block = None

        return True

    def draw_block(self, block, selected=False):
        """绘制一个方块"""
        color = WHITE

        # 根据方块类型设置颜色
        if block.type == BlockType.ORIGIN:
            color = GREEN
        elif block.type == BlockType.TERMINAL:
            color = RED
        elif block.static:
            color = DARK_GRAY
        else:
            color = GRAY

        # 绘制方块背景
        pygame.draw.rect(self.screen, color, block.rect)
        pygame.draw.rect(self.screen, BLACK, block.rect, 2)

        # 如果是选中的方块，高亮显示
        if selected:
            pygame.draw.rect(self.screen, BLUE, block.rect, 4)

        # 绘制通道
        center_x = block.rect.x + TILE_SIZE // 2
        center_y = block.rect.y + TILE_SIZE // 2
        channel_width = TILE_SIZE // 4

        # 绘制中心点（如果有）
        if block.channel_position & ChannelPosition.CENTER:
            pygame.draw.circle(self.screen, BLACK, (center_x, center_y), channel_width // 2)

        # 绘制向上通道
        if block.channel_position & ChannelPosition.UPWARDS:
            pygame.draw.rect(self.screen, BLACK,
                             (center_x - channel_width // 2,
                              block.rect.y,
                              channel_width,
                              TILE_SIZE // 2))

        # 绘制向下通道
        if block.channel_position & ChannelPosition.DOWNWARDS:
            pygame.draw.rect(self.screen, BLACK,
                             (center_x - channel_width // 2,
                              center_y,
                              channel_width,
                              TILE_SIZE // 2))

        # 绘制向左通道
        if block.channel_position & ChannelPosition.LEFTWARDS:
            pygame.draw.rect(self.screen, BLACK,
                             (block.rect.x,
                              center_y - channel_width // 2,
                              TILE_SIZE // 2,
                              channel_width))

        # 绘制向右通道
        if block.channel_position & ChannelPosition.RIGHTWARDS:
            pygame.draw.rect(self.screen, BLACK,
                             (center_x,
                              center_y - channel_width // 2,
                              TILE_SIZE // 2,
                              channel_width))

    def draw_grid(self):
        """绘制游戏网格"""
        if not self.current_level:
            return

        # 绘制网格线
        for row in range(self.current_level.rows + 1):
            y = GRID_OFFSET_Y + row * TILE_SIZE
            pygame.draw.line(self.screen, DARK_GRAY,
                             (GRID_OFFSET_X, y),
                             (GRID_OFFSET_X + self.current_level.cols * TILE_SIZE, y), 2)

        for col in range(self.current_level.cols + 1):
            x = GRID_OFFSET_X + col * TILE_SIZE
            pygame.draw.line(self.screen, DARK_GRAY,
                             (x, GRID_OFFSET_Y),
                             (x, GRID_OFFSET_Y + self.current_level.rows * TILE_SIZE), 2)

        # 绘制所有方块
        for block in self.current_level.blocks:
            selected = (block == self.selected_block)
            self.draw_block(block, selected)

    def draw_message_box(self):
        """绘制消息框"""
        if not self.show_message:
            return

        # 绘制半透明背景
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))  # 半透明黑色
        self.screen.blit(s, (0, 0))

        # 绘制消息框
        pygame.draw.rect(self.screen, WHITE, self.message_box_rect)
        pygame.draw.rect(self.screen, BLACK, self.message_box_rect, 3)

        # 根据消息类型绘制不同标题
        if self.message_type == "complete":
            title_color = GREEN
            title_text = "关卡完成"
        else:  # game_over
            title_color = RED
            title_text = "游戏结束"

        # 绘制标题
        title = self.font.render(title_text, True, title_color)
        title_rect = title.get_rect(center=(self.message_box_rect.centerx, self.message_box_rect.y + 40))
        self.screen.blit(title, title_rect)

        # 绘制消息文本
        lines = self.message_text.split('\n')
        for i, line in enumerate(lines):
            text = self.small_font.render(line, True, BLACK)
            text_rect = text.get_rect(center=(self.message_box_rect.centerx,
                                              self.message_box_rect.y + 80 + i * 30))
            self.screen.blit(text, text_rect)

        # 绘制按钮
        if self.message_type == "complete":
            # 关卡完成按钮：下一关、返回选关
            if self.current_level_index + 1 < len(self.levels):
                pygame.draw.rect(self.screen, GREEN, self.next_button)
                pygame.draw.rect(self.screen, BLACK, self.next_button, 2)
                next_text = self.small_font.render("下一关", True, WHITE)
                next_rect = next_text.get_rect(center=self.next_button.center)
                self.screen.blit(next_text, next_rect)

            pygame.draw.rect(self.screen, BLUE, self.return_complete_button)
            pygame.draw.rect(self.screen, BLACK, self.return_complete_button, 2)
            return_text = self.small_font.render("返回", True, WHITE)
            return_rect = return_text.get_rect(center=self.return_complete_button.center)
            self.screen.blit(return_text, return_rect)

        else:  # game_over
            # 游戏结束按钮：重试、返回选关
            pygame.draw.rect(self.screen, ORANGE, self.restart_button)
            pygame.draw.rect(self.screen, BLACK, self.restart_button, 2)
            restart_text = self.small_font.render("重试", True, WHITE)
            restart_rect = restart_text.get_rect(center=self.restart_button.center)
            self.screen.blit(restart_text, restart_rect)

            pygame.draw.rect(self.screen, BLUE, self.return_fail_button)
            pygame.draw.rect(self.screen, BLACK, self.return_fail_button, 2)
            return_text = self.small_font.render("返回", True, WHITE)
            return_rect = return_text.get_rect(center=self.return_fail_button.center)
            self.screen.blit(return_text, return_rect)

    def draw_ui(self):
        """绘制游戏UI"""
        if self.state == "level_select":
            self.draw_level_select_ui()
        elif self.state == "playing":
            self.draw_game_ui()

        # 如果有消息框，绘制消息框
        self.draw_message_box()

    def draw_level_select_ui(self):
        """绘制关卡选择界面"""
        self.screen.fill(BLACK)

        # 绘制标题
        title = self.title_font.render(f"管道连接小游戏 - 关卡选择 (第{self.current_page + 1}页)", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # 绘制当前页的关卡按钮
        for button, level_index in self.level_buttons:
            # 如果该关卡已通关，显示绿色，否则灰色
            color = GREEN if level_index in self.completed_levels else GRAY
            pygame.draw.rect(self.screen, color, button)
            pygame.draw.rect(self.screen, WHITE, button, 2)

            level_text = self.small_font.render(f"关卡 {level_index + 1}", True, BLACK)
            text_rect = level_text.get_rect(center=button.center)
            self.screen.blit(level_text, text_rect)

        # 绘制翻页按钮
        if self.current_page > 0:
            pygame.draw.rect(self.screen, BLUE, self.prev_button)
            pygame.draw.rect(self.screen, WHITE, self.prev_button, 2)
            prev_text = self.small_font.render("上一页", True, WHITE)
            prev_rect = prev_text.get_rect(center=self.prev_button.center)
            self.screen.blit(prev_text, prev_rect)

        if (self.current_page + 1) * self.levels_per_page < len(self.levels):
            pygame.draw.rect(self.screen, BLUE, self.next_button_page)
            pygame.draw.rect(self.screen, WHITE, self.next_button_page, 2)
            next_text = self.small_font.render("下一页", True, WHITE)
            next_rect = next_text.get_rect(center=self.next_button_page.center)
            self.screen.blit(next_text, next_rect)

        # 绘制说明 - 居中显示
        instructions = [
            f"已通关: {len(self.completed_levels)}/{len(self.levels)} 关",
            "选择关卡开始游戏",
            "游戏中可以拖动方块进行移动",
            "按R键重置当前关卡",
            "按Ctrl+Z键回退一步",
            "按ESC键返回关卡选择"
        ]

        # 计算总高度
        total_height = len(instructions) * 30
        start_y = SCREEN_HEIGHT - 180

        for i, text in enumerate(instructions):
            text_surface = self.small_font.render(text, True, WHITE)
            # 居中显示
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 30))
            self.screen.blit(text_surface, text_rect)

    def draw_game_ui(self):
        """绘制游戏界面"""
        self.screen.fill(BLACK)

        # 计算游戏区域的实际宽度，用于居中显示
        game_area_width = self.current_level.cols * TILE_SIZE
        # 重新计算水平偏移量，使游戏区域在UI面板左侧居中
        global GRID_OFFSET_X
        GRID_OFFSET_X = (SCREEN_WIDTH - UI_WIDTH - game_area_width) // 2

        # 更新所有方块的位置
        for block in self.current_level.blocks:
            block.update_position()

        # 绘制游戏区域背景
        game_bg = pygame.Rect(GRID_OFFSET_X - 10, GRID_OFFSET_Y - 10,
                              game_area_width + 20,
                              self.current_level.rows * TILE_SIZE + 20)
        pygame.draw.rect(self.screen, (50, 50, 50), game_bg)

        # 绘制网格和方块
        self.draw_grid()

        # 绘制UI面板
        ui_panel = pygame.Rect(SCREEN_WIDTH - UI_WIDTH, 0, UI_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, (40, 40, 40), ui_panel)

        # 绘制关卡信息
        level_text = self.font.render(f"关卡 {self.current_level_index + 1}", True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH - UI_WIDTH + 20, 30))

        # 绘制步数信息
        moves_text = self.font.render(f"步数: {self.current_level.current_moves}/{self.current_level.max_moves}", True,
                                      WHITE)
        self.screen.blit(moves_text, (SCREEN_WIDTH - UI_WIDTH + 20, 80))

        # 绘制状态信息
        status_text = ""
        status_color = WHITE

        if self.current_level.is_complete():
            status_text = "已连通"
            status_color = GREEN
        elif self.current_level.is_game_over():
            status_text = "步数用完"
            status_color = RED
        elif self.current_level.max_moves - self.current_level.current_moves <= 3:
            status_text = "步数紧张"
            status_color = ORANGE

        if status_text:
            status_surface = self.small_font.render(status_text, True, status_color)
            self.screen.blit(status_surface, (SCREEN_WIDTH - UI_WIDTH + 20, 130))

        # 绘制回退按钮
        pygame.draw.rect(self.screen, CYAN, self.undo_button)
        pygame.draw.rect(self.screen, WHITE, self.undo_button, 2)
        undo_text = self.small_font.render("回退一步", True, WHITE)
        undo_rect = undo_text.get_rect(center=self.undo_button.center)
        self.screen.blit(undo_text, undo_rect)

        # 绘制重置按钮
        pygame.draw.rect(self.screen, BLUE, self.reset_button)
        pygame.draw.rect(self.screen, WHITE, self.reset_button, 2)
        reset_text = self.small_font.render("重置关卡", True, WHITE)
        reset_rect = reset_text.get_rect(center=self.reset_button.center)
        self.screen.blit(reset_text, reset_rect)

        # 绘制返回按钮
        pygame.draw.rect(self.screen, PURPLE, self.back_button)
        pygame.draw.rect(self.screen, WHITE, self.back_button, 2)
        back_text = self.small_font.render("返回", True, WHITE)
        back_rect = back_text.get_rect(center=self.back_button.center)
        self.screen.blit(back_text, back_rect)

        # 绘制游戏说明
        instructions = [
            "游戏说明:",
            "- 拖动方块进行移动",
            "- 连接起点(绿色)和终点(红色)",
            "- 灰色方块可移动，深灰色方块固定",
            "- 直管: 上下或左右连接",
            "- 曲管: 转弯连接",
            "- 按R键: 重置关卡",
            "- 按Ctrl+Z键: 回退一步",
            "- 按ESC键: 返回关卡选择",
            "- 点击'回退一步'按钮撤销上一步"
        ]

        for i, text in enumerate(instructions):
            text_surface = self.small_font.render(text, True, WHITE)
            self.screen.blit(text_surface, (SCREEN_WIDTH - UI_WIDTH + 20, 200 + i * 25))

    def run(self):
        """运行游戏主循环"""
        running = True

        while running:
            running = self.handle_events()

            # 检查游戏状态
            if self.state == "playing" and self.current_level:
                # 首先检查是否通关
                if not self.game_won and self.current_level.is_complete():
                    self.game_won = True
                    self.show_complete_message()
                # 然后检查是否游戏结束（步数用完且未完成）
                elif not self.show_message and self.current_level.is_game_over() and not self.current_level.is_complete():
                    self.show_game_over_message()

            self.draw_ui()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# 启动游戏
if __name__ == "__main__":
    game = PipeGame()
    game.run()