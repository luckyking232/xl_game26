// ==================== 枚举 ====================
const BlockType = {
    NORMAL: 0,
    ORIGIN: 1,
    TERMINAL: 2
};

const ChannelPosition = {
    NONE: 0,
    CENTER: 1,
    UPWARDS: 2,
    DOWNWARDS: 4,
    LEFTWARDS: 8,
    RIGHTWARDS: 16
};

// ==================== 常量 ====================
const TILE_SIZE = 116;
let GRID_OFFSET_X = 100;
const GRID_OFFSET_Y = 50;
const UI_WIDTH = 300;
let CANVAS_WIDTH = 1200;
let CANVAS_HEIGHT = 800;
const FPS = 60;

// 颜色
const COLORS = {
    BLACK: '#000000',
    WHITE: '#FFFFFF',
    GRAY: '#C8C8C8',
    DARK_GRAY: '#646464',
    BLUE: '#1E90FF',
    GREEN: '#32CD32',
    RED: '#FF6347',
    PURPLE: '#9370DB',
    YELLOW: '#FFD700',
    ORANGE: '#FFA500',
    CYAN: '#00FFFF',
    BG_DARK: '#1a1a2e',
    PANEL_BG: '#282828',
    GRID_BG: '#323232'
};

// ==================== 方块类 ====================
class Block {
    constructor(type, channelPosition, row, col, isStatic = false, rotation = 0) {
        this.type = type;
        this.channelPosition = channelPosition;
        this.row = row;
        this.col = col;
        this.isStatic = isStatic;
        this.rotation = rotation;
        this.x = 0;
        this.y = 0;
        this.updatePosition();
    }

    updatePosition() {
        this.x = GRID_OFFSET_X + this.col * TILE_SIZE;
        this.y = GRID_OFFSET_Y + this.row * TILE_SIZE;
    }

    move(dRow, dCol) {
        if (!this.isStatic) {
            this.row += dRow;
            this.col += dCol;
            this.updatePosition();
            return true;
        }
        return false;
    }
}

// ==================== 关卡类 ====================
class Level {
    constructor(id, gameId, gridSize, maxMoves, dataPath) {
        this.id = id;
        this.gameId = gameId;
        this.rows = gridSize[0];
        this.cols = gridSize[1];
        this.maxMoves = maxMoves;
        this.dataPath = dataPath;
        this.blocks = [];
        this.origin = null;
        this.terminal = null;
        this.currentMoves = 0;
        this.moveHistory = [];
        this.parseDataPath();
    }

    parseConfigStr(configStr) {
        const splits = configStr.split('|');
        const itemConfigs = [];

        for (const split of splits) {
            const subsplits = split.split(':');
            if (subsplits.length < 4) continue;

            const x = parseInt(subsplits[0]);
            const y = parseInt(subsplits[1]);
            const bType = parseInt(subsplits[2]);
            const bPosition = parseInt(subsplits[3]);
            const rotation = subsplits.length > 4 ? parseInt(subsplits[4]) : 0;

            const conf = {
                row: y - 1,
                col: x - 1,
                static: false,
                channelPosition: ChannelPosition.NONE,
                type: BlockType.NORMAL
            };

            if (bPosition === 4 || bPosition === 5) {
                conf.static = true;
                if (rotation === 1) conf.channelPosition = ChannelPosition.CENTER | ChannelPosition.UPWARDS;
                else if (rotation === 2) conf.channelPosition = ChannelPosition.CENTER | ChannelPosition.RIGHTWARDS;
                else if (rotation === 3) conf.channelPosition = ChannelPosition.CENTER | ChannelPosition.DOWNWARDS;
                else if (rotation === 4) conf.channelPosition = ChannelPosition.CENTER | ChannelPosition.LEFTWARDS;
                else conf.channelPosition = ChannelPosition.CENTER | ChannelPosition.DOWNWARDS;

                conf.type = bPosition === 4 ? BlockType.ORIGIN : BlockType.TERMINAL;
            } else if (bPosition === 1) {
                conf.type = BlockType.NORMAL;
                conf.channelPosition = ChannelPosition.NONE;
                conf.static = (bType === 3);
            } else if (bPosition === 2) {
                conf.type = BlockType.NORMAL;
                conf.static = (bType === 3);
                if (rotation === 1 || rotation === 3)
                    conf.channelPosition = ChannelPosition.UPWARDS | ChannelPosition.DOWNWARDS;
                else if (rotation === 2 || rotation === 4)
                    conf.channelPosition = ChannelPosition.LEFTWARDS | ChannelPosition.RIGHTWARDS;
            } else if (bPosition === 3) {
                conf.type = BlockType.NORMAL;
                conf.static = (bType === 3);
                if (rotation === 1) conf.channelPosition = ChannelPosition.UPWARDS | ChannelPosition.RIGHTWARDS;
                else if (rotation === 2) conf.channelPosition = ChannelPosition.RIGHTWARDS | ChannelPosition.DOWNWARDS;
                else if (rotation === 3) conf.channelPosition = ChannelPosition.DOWNWARDS | ChannelPosition.LEFTWARDS;
                else if (rotation === 4) conf.channelPosition = ChannelPosition.LEFTWARDS | ChannelPosition.UPWARDS;
            }

            itemConfigs.push(conf);
        }
        return itemConfigs;
    }

    parseDataPath() {
        const itemConfigs = this.parseConfigStr(this.dataPath);
        this.blocks = [];
        for (const conf of itemConfigs) {
            const block = new Block(conf.type, conf.channelPosition, conf.row, conf.col, conf.static, 0);
            this.blocks.push(block);
            if (conf.type === BlockType.ORIGIN) this.origin = block;
            else if (conf.type === BlockType.TERMINAL) this.terminal = block;
        }
    }

    getBlockAt(row, col) { return this.blocks.find(b => b.row === row && b.col === col) || null; }

    canMoveTo(block, dRow, dCol) {
        const newRow = block.row + dRow;
        const newCol = block.col + dCol;
        return newRow >= 0 && newRow < this.rows && newCol >= 0 && newCol < this.cols && !this.getBlockAt(newRow, newCol);
    }

    moveBlock(block, dRow, dCol) {
        if (!block.isStatic && this.canMoveTo(block, dRow, dCol)) {
            const oldRow = block.row, oldCol = block.col;
            block.move(dRow, dCol);
            this.currentMoves++;
            this.moveHistory.push({ block, oldRow, oldCol, newRow: block.row, newCol: block.col });
            return true;
        }
        return false;
    }

    undoMove() {
        if (this.moveHistory.length === 0 || this.currentMoves === 0) return false;
        const last = this.moveHistory.pop();
        last.block.row = last.oldRow;
        last.block.col = last.oldCol;
        last.block.updatePosition();
        this.currentMoves--;
        return true;
    }

    reset() {
        this.currentMoves = 0;
        this.moveHistory = [];
        this.blocks = [];
        this.origin = null;
        this.terminal = null;
        this.parseDataPath();
    }

    areBlocksConnected(block1, block2, dRow, dCol) {
        let block1Open = false, block2Open = false;
        if (dRow === -1) block1Open = !!(block1.channelPosition & ChannelPosition.UPWARDS);
        else if (dRow === 1) block1Open = !!(block1.channelPosition & ChannelPosition.DOWNWARDS);
        else if (dCol === -1) block1Open = !!(block1.channelPosition & ChannelPosition.LEFTWARDS);
        else if (dCol === 1) block1Open = !!(block1.channelPosition & ChannelPosition.RIGHTWARDS);

        if (dRow === -1) block2Open = !!(block2.channelPosition & ChannelPosition.DOWNWARDS);
        else if (dRow === 1) block2Open = !!(block2.channelPosition & ChannelPosition.UPWARDS);
        else if (dCol === -1) block2Open = !!(block2.channelPosition & ChannelPosition.RIGHTWARDS);
        else if (dCol === 1) block2Open = !!(block2.channelPosition & ChannelPosition.LEFTWARDS);

        return block1Open && block2Open;
    }

    checkConnection() {
        if (!this.origin || !this.terminal) return false;
        const visited = new Set();
        const dfs = (block) => {
            if (block === this.terminal) return true;
            if (visited.has(block)) return false;
            visited.add(block);
            const directions = [];
            if (block.channelPosition & ChannelPosition.UPWARDS) directions.push([-1, 0]);
            if (block.channelPosition & ChannelPosition.DOWNWARDS) directions.push([1, 0]);
            if (block.channelPosition & ChannelPosition.LEFTWARDS) directions.push([0, -1]);
            if (block.channelPosition & ChannelPosition.RIGHTWARDS) directions.push([0, 1]);
            for (const [dRow, dCol] of directions) {
                const newRow = block.row + dRow, newCol = block.col + dCol;
                if (newRow >= 0 && newRow < this.rows && newCol >= 0 && newCol < this.cols) {
                    const neighbor = this.getBlockAt(newRow, newCol);
                    if (neighbor && this.areBlocksConnected(block, neighbor, dRow, dCol)) {
                        if (dfs(neighbor)) return true;
                    }
                }
            }
            visited.delete(block);
            return false;
        };
        return dfs(this.origin);
    }

    isComplete() { return this.checkConnection(); }
    isGameOver() { return this.currentMoves >= this.maxMoves && !this.checkConnection(); }
}

// ==================== 主游戏类 ====================
class PipeGame {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        // 初始化画布尺寸为设计尺寸 1200x800
        canvas.width = CANVAS_WIDTH;
        canvas.height = CANVAS_HEIGHT;

        // 使用独立的关卡数据 LEVELS_DATA
        this.levels = [];
        this.loadLevels();

        // 状态
        this.state = 'levelSelect';
        this.currentLevelIndex = 0;
        this.currentLevel = null;
        this.selectedBlock = null;
        this.dragStartPos = null;
        this.gameWon = false;
        this.showMessage = false;
        this.messageText = '';
        this.messageType = '';

        this.currentPage = 0;
        this.levelsPerPage = 20;
        this.completedLevels = new Set();

        this.buttons = {};
        this.initButtons();

        this.lastTime = 0;
        this.fpsInterval = 1000 / FPS;
        this.then = performance.now();
        this.bindEvents();
        this.gameLoop(0);
    }

    initButtons() {
        // 这些按钮位置固定使用 CANVAS_WIDTH / CANVAS_HEIGHT
        this.buttons.undo = { x: CANVAS_WIDTH - 250, y: CANVAS_HEIGHT - 160, w: 100, h: 40 };
        this.buttons.reset = { x: CANVAS_WIDTH - 250, y: CANVAS_HEIGHT - 110, w: 100, h: 40 };
        this.buttons.back = { x: CANVAS_WIDTH - 250, y: CANVAS_HEIGHT - 60, w: 100, h: 40 };
        this.buttons.nextLevel = null;
        this.buttons.returnComplete = null;
        this.buttons.retry = null;
        this.buttons.returnFail = null;
        this.buttons.prevPage = { x: 50, y: CANVAS_HEIGHT - 60, w: 80, h: 40 };
        this.buttons.nextPage = { x: CANVAS_WIDTH - 130, y: CANVAS_HEIGHT - 60, w: 80, h: 40 };
    }

    // 使用 LEVELS_DATA 构建关卡
    loadLevels() {
        for (const data of LEVELS_DATA) {
            const level = new Level(data.id, data.game_id, data.grid, data.site[0], data.data_path);
            this.levels.push(level);
        }
    }

    // ==================== 事件绑定（未变，省略详细代码，与之前相同） ====================
    bindEvents() {
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
        this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        this.canvas.addEventListener('touchend', (e) => this.handleTouchEnd(e));
    }

    getCanvasPos(e) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY
        };
    }

    handleMouseDown(e) { const pos = this.getCanvasPos(e); this.handlePointerDown(pos); }
    handleTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        this.handlePointerDown(this.getCanvasPos(touch));
    }

    handlePointerDown(pos) {
        if (this.showMessage) {
            this.checkMessageBoxButtons(pos);
            return;
        }

        if (this.state === 'levelSelect') {
            this.checkLevelSelectButtons(pos);
        } else if (this.state === 'playing') {
            if (this.isInside(pos, this.buttons.undo)) {
                this.currentLevel.undoMove(); this.selectedBlock = null; this.gameWon = false; return;
            }
            if (this.isInside(pos, this.buttons.reset)) {
                this.currentLevel.reset(); this.selectedBlock = null; this.gameWon = false; return;
            }
            if (this.isInside(pos, this.buttons.back)) {
                this.state = 'levelSelect'; this.selectedBlock = null; return;
            }

            for (const block of this.currentLevel.blocks) {
                if (!block.isStatic && pos.x >= block.x && pos.x < block.x + TILE_SIZE &&
                    pos.y >= block.y && pos.y < block.y + TILE_SIZE) {
                    this.selectedBlock = block;
                    this.dragStartPos = { x: pos.x, y: pos.y };
                    break;
                }
            }
        }
    }

    handleMouseMove(e) { /* 空 */ }
    handleTouchMove(e) { e.preventDefault(); }

    handleMouseUp(e) { this.handlePointerUp(this.getCanvasPos(e)); }
    handleTouchEnd(e) {
        this.handlePointerUp(this.dragStartPos || { x: 0, y: 0 });
    }

    handlePointerUp(pos) {
        if (this.selectedBlock && this.dragStartPos) {
            const dx = pos.x - this.dragStartPos.x;
            const dy = pos.y - this.dragStartPos.y;
            if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 20) {
                const dCol = dx > 0 ? 1 : -1;
                this.currentLevel.moveBlock(this.selectedBlock, 0, dCol);
            } else if (Math.abs(dy) > 20) {
                const dRow = dy > 0 ? 1 : -1;
                this.currentLevel.moveBlock(this.selectedBlock, dRow, 0);
            }
            this.selectedBlock = null;
            this.dragStartPos = null;
        }
    }

    isInside(pos, rect) {
        return rect && pos.x >= rect.x && pos.x <= rect.x + rect.w && pos.y >= rect.y && pos.y <= rect.y + rect.h;
    }

    // 关卡选择按钮计算（动态居中）
    getLevelButtonRect(index) {
        const start = this.currentPage * this.levelsPerPage;
        const relIdx = index - start;
        const row = Math.floor(relIdx / 5);
        const col = relIdx % 5;
        const btnW = 100, btnH = 40, gapX = 20, gapY = 20;
        const totalWidth = 5 * btnW + 4 * gapX;  // 580
        const startX = (CANVAS_WIDTH - totalWidth) / 2;
        const startY = 150;
        return {
            x: startX + col * (btnW + gapX),
            y: startY + row * (btnH + gapY),
            w: btnW,
            h: btnH
        };
    }

    checkLevelSelectButtons(pos) {
        const start = this.currentPage * this.levelsPerPage;
        const end = Math.min(start + this.levelsPerPage, this.levels.length);
        for (let i = start; i < end; i++) {
            const btn = this.getLevelButtonRect(i);
            if (this.isInside(pos, btn)) {
                this.startLevel(i);
                return;
            }
        }
        if (this.currentPage > 0 && this.isInside(pos, this.buttons.prevPage)) this.currentPage--;
        else if (end < this.levels.length && this.isInside(pos, this.buttons.nextPage)) this.currentPage++;
    }

    checkMessageBoxButtons(pos) {
        if (this.messageType === 'complete') {
            if (this.buttons.nextLevel && this.isInside(pos, this.buttons.nextLevel)) this.nextLevel();
            else if (this.buttons.returnComplete && this.isInside(pos, this.buttons.returnComplete)) {
                this.state = 'levelSelect'; this.showMessage = false;
            }
        } else if (this.messageType === 'gameOver') {
            if (this.buttons.retry && this.isInside(pos, this.buttons.retry)) {
                this.currentLevel.reset(); this.gameWon = false; this.showMessage = false;
            } else if (this.buttons.returnFail && this.isInside(pos, this.buttons.returnFail)) {
                this.state = 'levelSelect'; this.showMessage = false;
            }
        }
    }

    startLevel(index) {
        this.currentLevelIndex = index;
        this.currentLevel = this.levels[index];
        this.currentLevel.reset();
        this.selectedBlock = null;
        this.dragStartPos = null;
        this.gameWon = false;
        this.showMessage = false;
        this.state = 'playing';
    }

    showCompleteMessage() {
        this.showMessage = true;
        this.messageText = `恭喜！\n你通过了第 ${this.currentLevelIndex + 1} 关！`;
        this.messageType = 'complete';
        this.completedLevels.add(this.currentLevelIndex);
    }

    showGameOverMessage() {
        this.showMessage = true;
        this.messageText = `步数已用完！\n你未能通过第 ${this.currentLevelIndex + 1} 关。`;
        this.messageType = 'gameOver';
    }

    nextLevel() {
        if (this.currentLevelIndex + 1 < this.levels.length) this.startLevel(this.currentLevelIndex + 1);
        else { this.state = 'levelSelect'; this.showMessage = false; }
    }

    // ==================== 绘图函数 ====================
    drawBlock(block, selected = false) {
        const ctx = this.ctx;
        let color = COLORS.GRAY;
        if (block.type === BlockType.ORIGIN) color = COLORS.GREEN;
        else if (block.type === BlockType.TERMINAL) color = COLORS.RED;
        else if (block.isStatic) color = COLORS.DARK_GRAY;

        ctx.fillStyle = color;
        ctx.fillRect(block.x, block.y, TILE_SIZE, TILE_SIZE);
        ctx.strokeStyle = COLORS.BLACK;
        ctx.lineWidth = 2;
        ctx.strokeRect(block.x, block.y, TILE_SIZE, TILE_SIZE);

        if (selected) {
            ctx.strokeStyle = COLORS.BLUE;
            ctx.lineWidth = 4;
            ctx.strokeRect(block.x, block.y, TILE_SIZE, TILE_SIZE);
        }

        const cx = block.x + TILE_SIZE / 2;
        const cy = block.y + TILE_SIZE / 2;
        const chW = TILE_SIZE / 4;
        ctx.fillStyle = COLORS.BLACK;

        if (block.channelPosition & ChannelPosition.CENTER) {
            ctx.beginPath();
            ctx.arc(cx, cy, chW / 2, 0, Math.PI * 2);
            ctx.fill();
        }
        if (block.channelPosition & ChannelPosition.UPWARDS) ctx.fillRect(cx - chW / 2, block.y, chW, TILE_SIZE / 2);
        if (block.channelPosition & ChannelPosition.DOWNWARDS) ctx.fillRect(cx - chW / 2, cy, chW, TILE_SIZE / 2);
        if (block.channelPosition & ChannelPosition.LEFTWARDS) ctx.fillRect(block.x, cy - chW / 2, TILE_SIZE / 2, chW);
        if (block.channelPosition & ChannelPosition.RIGHTWARDS) ctx.fillRect(cx, cy - chW / 2, TILE_SIZE / 2, chW);
    }

    drawGrid() {
        if (!this.currentLevel) return;
        const ctx = this.ctx;
        const level = this.currentLevel;
        ctx.strokeStyle = COLORS.DARK_GRAY;
        ctx.lineWidth = 2;
        for (let row = 0; row <= level.rows; row++) {
            const y = GRID_OFFSET_Y + row * TILE_SIZE;
            ctx.beginPath();
            ctx.moveTo(GRID_OFFSET_X, y);
            ctx.lineTo(GRID_OFFSET_X + level.cols * TILE_SIZE, y);
            ctx.stroke();
        }
        for (let col = 0; col <= level.cols; col++) {
            const x = GRID_OFFSET_X + col * TILE_SIZE;
            ctx.beginPath();
            ctx.moveTo(x, GRID_OFFSET_Y);
            ctx.lineTo(x, GRID_OFFSET_Y + level.rows * TILE_SIZE);
            ctx.stroke();
        }

        for (const block of level.blocks) this.drawBlock(block, block === this.selectedBlock);
    }

    drawLevelSelect() {
        const ctx = this.ctx;
        ctx.fillStyle = COLORS.BG_DARK;
        ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

        ctx.font = '36px "Microsoft YaHei", "SimHei", sans-serif';
        ctx.fillStyle = COLORS.WHITE;
        ctx.textAlign = 'center';
        ctx.fillText(`管道连接小游戏 - 关卡选择 (第${this.currentPage + 1}页)`, CANVAS_WIDTH / 2, 80);

        const start = this.currentPage * this.levelsPerPage;
        const end = Math.min(start + this.levelsPerPage, this.levels.length);
        for (let i = start; i < end; i++) {
            const btn = this.getLevelButtonRect(i);
            ctx.fillStyle = this.completedLevels.has(i) ? COLORS.GREEN : COLORS.GRAY;
            ctx.fillRect(btn.x, btn.y, btn.w, btn.h);
            ctx.strokeStyle = COLORS.WHITE;
            ctx.lineWidth = 2;
            ctx.strokeRect(btn.x, btn.y, btn.w, btn.h);

            ctx.font = '20px "Microsoft YaHei", "SimHei", sans-serif';
            ctx.fillStyle = COLORS.BLACK;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(`关卡 ${i + 1}`, btn.x + btn.w / 2, btn.y + btn.h / 2);
        }

        if (this.currentPage > 0) this.drawButton(this.buttons.prevPage, '上一页', COLORS.BLUE);
        if (end < this.levels.length) this.drawButton(this.buttons.nextPage, '下一页', COLORS.BLUE);

        // 底部操作提示
        ctx.font = '20px "Microsoft YaHei", "SimHei", sans-serif';
        ctx.fillStyle = COLORS.WHITE;
        ctx.textAlign = 'center';
        ctx.fillText(`已通关: ${this.completedLevels.size}/${this.levels.length}  选择关卡开始游戏`, CANVAS_WIDTH / 2, CANVAS_HEIGHT - 100);
        ctx.textAlign = 'left';
    }

    drawGameUI() {
        const ctx = this.ctx;
        ctx.fillStyle = COLORS.BG_DARK;
        ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

        if (!this.currentLevel) return;
        const level = this.currentLevel;
        const gameWidth = level.cols * TILE_SIZE;
        GRID_OFFSET_X = (CANVAS_WIDTH - UI_WIDTH - gameWidth) / 2;
        for (const block of level.blocks) block.updatePosition();

        ctx.fillStyle = COLORS.GRID_BG;
        ctx.fillRect(GRID_OFFSET_X - 10, GRID_OFFSET_Y - 10, gameWidth + 20, level.rows * TILE_SIZE + 20);
        this.drawGrid();

        ctx.fillStyle = COLORS.PANEL_BG;
        ctx.fillRect(CANVAS_WIDTH - UI_WIDTH, 0, UI_WIDTH, CANVAS_HEIGHT);

        ctx.font = '28px "Microsoft YaHei", "SimHei", sans-serif';
        ctx.fillStyle = COLORS.WHITE;
        ctx.textAlign = 'left';
        ctx.fillText(`关卡 ${this.currentLevelIndex + 1}`, CANVAS_WIDTH - UI_WIDTH + 20, 40);
        ctx.fillText(`步数: ${level.currentMoves}/${level.maxMoves}`, CANVAS_WIDTH - UI_WIDTH + 20, 90);

        if (level.isComplete()) {
            ctx.fillStyle = COLORS.GREEN;
            ctx.fillText('已连通', CANVAS_WIDTH - UI_WIDTH + 20, 140);
        } else if (level.isGameOver()) {
            ctx.fillStyle = COLORS.RED;
            ctx.fillText('步数用完', CANVAS_WIDTH - UI_WIDTH + 20, 140);
        }

        this.drawButton(this.buttons.undo, '回退一步', COLORS.CYAN);
        this.drawButton(this.buttons.reset, '重置关卡', COLORS.BLUE);
        this.drawButton(this.buttons.back, '返回', COLORS.PURPLE);

        // 新增：操作提示区域
        const tipX = CANVAS_WIDTH - UI_WIDTH + 20;
        let tipY = 200;
        ctx.font = '18px "Microsoft YaHei", "SimHei", sans-serif';
        ctx.fillStyle = COLORS.WHITE;
        const tips = [
            '操作说明：',
            '· 拖动灰色方块移动',
            '· 连接绿色起点与红色终点',
            '· 深灰色方块为固定障碍',
            '· 按R键重置关卡',
            '· 按Ctrl+Z回退一步',
            '· 按ESC返回关卡选择'
        ];
        for (const tip of tips) {
            ctx.fillText(tip, tipX, tipY);
            tipY += 25;
        }
    }

    drawButton(rect, text, color) {
        if (!rect) return;
        const ctx = this.ctx;
        ctx.fillStyle = color;
        ctx.fillRect(rect.x, rect.y, rect.w, rect.h);
        ctx.strokeStyle = COLORS.WHITE;
        ctx.lineWidth = 2;
        ctx.strokeRect(rect.x, rect.y, rect.w, rect.h);
        ctx.font = '20px "Microsoft YaHei", "SimHei", sans-serif';
        ctx.fillStyle = COLORS.WHITE;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, rect.x + rect.w / 2, rect.y + rect.h / 2);
    }

    drawMessageBox() {
        if (!this.showMessage) return;
        const ctx = this.ctx;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

        const boxW = 400, boxH = 200;
        const boxX = (CANVAS_WIDTH - boxW) / 2;
        const boxY = (CANVAS_HEIGHT - boxH) / 2;
        ctx.fillStyle = COLORS.WHITE;
        ctx.fillRect(boxX, boxY, boxW, boxH);
        ctx.strokeStyle = COLORS.BLACK;
        ctx.strokeRect(boxX, boxY, boxW, boxH);

        const titleColor = this.messageType === 'complete' ? COLORS.GREEN : COLORS.RED;
        const titleText = this.messageType === 'complete' ? '关卡完成' : '游戏结束';
        ctx.font = '28px "Microsoft YaHei", "SimHei", sans-serif';
        ctx.fillStyle = titleColor;
        ctx.textAlign = 'center';
        ctx.fillText(titleText, boxX + boxW / 2, boxY + 40);

        const lines = this.messageText.split('\n');
        ctx.font = '20px "Microsoft YaHei", "SimHei", sans-serif';
        ctx.fillStyle = COLORS.BLACK;
        for (let i = 0; i < lines.length; i++) ctx.fillText(lines[i], boxX + boxW / 2, boxY + 80 + i * 30);

        if (this.messageType === 'complete') {
            this.buttons.nextLevel = this.currentLevelIndex + 1 < this.levels.length ? { x: boxX + 120, y: boxY + 130, w: 80, h: 40 } : null;
            this.buttons.returnComplete = { x: boxX + 280, y: boxY + 130, w: 80, h: 40 };
            if (this.buttons.nextLevel) this.drawButton(this.buttons.nextLevel, '下一关', COLORS.GREEN);
            this.drawButton(this.buttons.returnComplete, '返回', COLORS.BLUE);
        } else {
            this.buttons.retry = { x: boxX + 120, y: boxY + 130, w: 80, h: 40 };
            this.buttons.returnFail = { x: boxX + 280, y: boxY + 130, w: 80, h: 40 };
            this.drawButton(this.buttons.retry, '重试', COLORS.ORANGE);
            this.drawButton(this.buttons.returnFail, '返回', COLORS.BLUE);
        }
    }

    update() {
        if (this.state === 'playing' && this.currentLevel) {
            if (!this.gameWon && this.currentLevel.isComplete()) {
                this.gameWon = true;
                this.showCompleteMessage();
            } else if (!this.showMessage && this.currentLevel.isGameOver() && !this.currentLevel.isComplete()) {
                this.showGameOverMessage();
            }
        }
    }

    draw() {
        this.ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        if (this.state === 'levelSelect') this.drawLevelSelect();
        else if (this.state === 'playing') this.drawGameUI();
        this.drawMessageBox();
    }

    gameLoop(now) {
        requestAnimationFrame((t) => this.gameLoop(t));
        const elapsed = now - this.then;
        if (elapsed > this.fpsInterval) {
            this.then = now - (elapsed % this.fpsInterval);
            this.update();
            this.draw();
        }
    }
}

// ==================== 启动 ====================
window.onload = () => {
    const canvas = document.getElementById('gameCanvas');
    new PipeGame(canvas);
};