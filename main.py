import os
import sys
import random
import time
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class DesktopPet(QWidget):
    def __init__(self, parent=None, **kwargs):
        super(DesktopPet, self).__init__(parent)
        # 初始化拖动相关状态变量
        self.is_follow_mouse = False
        self.mouse_drag_pos = QPoint()
        # 窗体初始化
        self.init()
        # 托盘化初始
        self.initPall()
        # 宠物静态gif图加载（增加路径容错）
        self.initPetImage()
        # 宠物正常待机，实现随机切换动作
        self.petNormalAction()

    # 窗体初始化
    def init(self):
        # 设置窗口属性:无边框、置顶、子窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        # 透明背景设置
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 重绘组件
        self.repaint()

    # 托盘化设置初始化（增加图标容错）
    def initPall(self):
        # 托盘图标路径容错：优先使用jpg，不存在则用系统默认图标
        icon_path = "tigerIcon.jpg"
        if not os.path.exists(icon_path):
            # 无自定义图标时使用系统默认图标
            self.tray_icon = QSystemTrayIcon(QApplication.style().standardIcon(QStyle.SP_ComputerIcon), self)
        else:
            self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)

        # 托盘菜单设置（移除"故事大会"选项）
        quit_action = QAction('退出', self, triggered=self.quit)
        showing = QAction('显示', self, triggered=self.showwin)
        # 绑定图标（存在时才设置）
        if os.path.exists(icon_path):
            quit_action.setIcon(QIcon(icon_path))
            showing.setIcon(QIcon(icon_path))

        # 构建托盘菜单
        self.tray_icon_menu = QMenu(self)
        self.tray_icon_menu.addAction(quit_action)
        self.tray_icon_menu.addAction(showing)
        self.tray_icon.setContextMenu(self.tray_icon_menu)
        # 显示托盘图标并提示启动成功
        self.tray_icon.show()
        self.tray_icon.showMessage("提示", "皮卡丘桌面宠物已启动～", QSystemTrayIcon.Information, 2000)

    # 宠物静态gif图加载（增加路径容错和中文编码兼容）
    def initPetImage(self):
        # 对话框定义（修复文字显示问题：文字与背景区分）
        self.talkLabel = QLabel(self)
        self.talkLabel.setStyleSheet("""
            font: bold 15pt '楷体';
            color: #FF6B6B;
            background-color: rgba(255,255,255,0.8);
            border-radius: 8px;
            padding: 5px 10px;
            border: 1px solid #E0E0E0;
        """)

        # 定义显示图片部分
        self.image = QLabel(self)
        self.movie = QMovie()
        self.image.setMovie(self.movie)
        # 初始加载动画（容错处理）
        default_gif = "pikaqiu/pikaqiu1.gif"
        if os.path.exists(default_gif):
            self.movie.setFileName(default_gif)
            self.movie.setScaledSize(QSize(200, 200))
            self.movie.start()
        else:
            # 无初始动画时显示提示文字
            self.image.setText("暂无动画资源")
            self.image.setStyleSheet("font: 12pt '楷体'; color: #999;")
            self.image.setAlignment(Qt.AlignCenter)

        self.resize(300, 300)

        # "休息一下"时间显示（优化样式）
        self.show_time_rest = QLabel(self)
        self.show_time_rest.setStyleSheet("""
            font: bold 25pt '楷体';
            color: #4ECDC4;
            background-color: rgba(255,255,255,0.9);
            border-radius: 10px;
            padding: 8px 15px;
            border: 2px solid #45B7D1;
        """)

        # 调用自定义的randomPosition，会使得宠物出现位置随机
        self.randomPosition()

        # 布局设置（垂直居中）
        vbox = QVBoxLayout()
        vbox.addWidget(self.talkLabel, alignment=Qt.AlignCenter)
        vbox.addWidget(self.image, alignment=Qt.AlignCenter)
        vbox.addWidget(self.show_time_rest, alignment=Qt.AlignCenter)
        self.setLayout(vbox)
        self.show()

        # 将宠物正常待机状态的动图放入pet1中（仅加载gif文件，增加容错）
        self.pet1 = []
        pikaqiu_dir = "pikaqiu"
        if os.path.isdir(pikaqiu_dir):
            for file_name in os.listdir(pikaqiu_dir):
                file_path = os.path.join(pikaqiu_dir, file_name)
                # 只加载gif格式文件，避免非动画文件报错
                if file_path.lower().endswith(('.gif', '.GIF')):
                    self.pet1.append(file_path)

        # 将宠物正常待机状态的对话放入dialog中（增加文件容错和中文编码）
        self.dialog = [
            "你好呀～", "今天也要加油！", "摸我会咬你哦～",
            "工作累了吧？", "记得多喝水～", "要不要一起玩？"
        ]
        dialog_file = "dialog.txt"
        if os.path.exists(dialog_file):
            try:
                # 用utf-8编码打开，避免中文乱码
                with open(dialog_file, "r", encoding="utf-8") as f:
                    text = f.read()
                    # 以换行符为分隔符，过滤空行
                    self.dialog = [line.strip() for line in text.split("\n") if line.strip()]
            except Exception as e:
                print(f"读取对话文件失败：{e}，使用默认对话")

    # 宠物正常待机动作
    def petNormalAction(self):
        # 每隔一段时间做个动作（定时器设置）
        self.timer = QTimer()
        self.timer.timeout.connect(self.randomAct)
        self.timer.start(5000)  # 5秒切换一次动作
        # 宠物状态设置为正常（0:正常待机 1:点击反馈 2:休息提醒）
        self.condition = 0

        # 每隔一段时间切换对话
        self.talkTimer = QTimer()
        self.talkTimer.timeout.connect(self.talk)
        self.talkTimer.start(5000)  # 5秒切换一次对话
        # 对话状态设置为常态（0:随机对话 1:交互对话）
        self.talk_condition = 0
        # 初始显示对话
        self.talk()

        # 休息提醒定时器（默认关闭）
        self.timer_rest = QTimer()
        self.timer_rest.timeout.connect(self.haveRest)
        self.rest_open = 1  # 1:休息提醒关闭 2:休息提醒打开

    # 随机动作切换（增加容错，避免无动画时报错）
    def randomAct(self):
        # 宠物状态为0时，代表正常待机，随机切换动画
        if self.condition == 0 and self.pet1:
            self.movie.stop()
            self.movie.setFileName(random.choice(self.pet1))
            self.movie.setScaledSize(QSize(200, 200))
            self.image.setMovie(self.movie)
            self.movie.start()

        # 宠物状态为1时，代表点击反馈，显示特定动画后恢复正常
        elif self.condition == 1:
            click_gif = "./click/click.gif"
            if os.path.exists(click_gif):
                self.movie.stop()
                self.movie.setFileName(click_gif)
                self.movie.setScaledSize(QSize(200, 200))
                self.image.setMovie(self.movie)
                self.movie.start()
            # 1秒后恢复正常待机状态
            QTimer.singleShot(1000, lambda: setattr(self, "condition", 0))
            self.talk_condition = 0

        # 宠物状态为2时，代表休息提醒，显示固定动画
        elif self.condition == 2:
            rest_gif = "./click/20220614223056.gif"
            if os.path.exists(rest_gif):
                self.movie.stop()
                self.movie.setFileName(rest_gif)
                self.movie.setScaledSize(QSize(200, 200))
                self.image.setMovie(self.movie)
                self.movie.start()
            # 无休息动画时，用随机待机动画替代
            elif self.pet1:
                self.movie.stop()
                self.movie.setFileName(random.choice(self.pet1))
                self.movie.setScaledSize(QSize(200, 200))
                self.image.setMovie(self.movie)
                self.movie.start()

    # 宠物对话框行为处理
    def talk(self):
        if not self.talk_condition:
            # talk_condition为0则选取加载在dialog中的随机语句
            self.talkLabel.setText(random.choice(self.dialog))
        else:
            # talk_condition为1显示点击交互对话
            self.talkLabel.setText("咬你哦！别碰我～")
        # 根据内容自适应大小
        self.talkLabel.adjustSize()

    # 退出操作，关闭程序（释放资源）
    def quit(self):
        self.timer.stop()
        self.talkTimer.stop()
        self.timer_rest.stop()
        self.tray_icon.hide()
        self.close()
        sys.exit()

    # 显示宠物（恢复透明度）
    def showwin(self):
        self.setWindowOpacity(1)
        self.raise_()  # 确保宠物窗口置顶显示

    # 宠物随机位置（确保不超出屏幕）
    def randomPosition(self):
        # 获取屏幕尺寸（适配多屏幕）
        screen_geo = QGuiApplication.primaryScreen().geometry()
        # 获取宠物窗口尺寸
        pet_geo = self.geometry()
        # 计算最大可移动范围（避免宠物超出屏幕）
        max_x = screen_geo.width() - pet_geo.width()
        max_y = screen_geo.height() - pet_geo.height()
        # 生成随机位置（确保在屏幕内）
        x = random.randint(0, max_x) if max_x > 0 else 0
        y = random.randint(0, max_y) if max_y > 0 else 0
        self.move(x, y)

    # 鼠标左键按下时, 宠物与鼠标位置绑定并触发交互
    def mousePressEvent(self, event):
        # 更改宠物状态为点击反馈
        self.condition = 1
        # 更改宠物对话状态为交互模式
        self.talk_condition = 1
        # 触发对话更新
        self.talk()
        # 触发动画更新
        self.randomAct()

        if event.button() == Qt.LeftButton:
            self.is_follow_mouse = True
        # 记录鼠标与宠物窗口的相对位置
        self.mouse_drag_pos = event.globalPos() - self.pos()
        event.accept()
        # 拖动时鼠标图形设置为"开手"
        self.setCursor(QCursor(Qt.OpenHandCursor))

        # 取消休息状态提示
        self.show_time_rest.setText("")

    # 鼠标移动时调用，实现宠物随鼠标移动
    def mouseMoveEvent(self, event):
        # 如果鼠标左键按下且处于绑定状态，跟随鼠标移动
        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
        event.accept()

    # 鼠标释放调用，取消绑定
    def mouseReleaseEvent(self, event):
        self.is_follow_mouse = False
        # 鼠标图形恢复为箭头
        self.setCursor(QCursor(Qt.ArrowCursor))
        event.accept()

    # 鼠标移进时调用，更改鼠标样式
    def enterEvent(self, event):
        # 设置鼠标形状为"合手"
        self.setCursor(Qt.ClosedHandCursor)
        event.accept()

    # 宠物右键点击交互（移除"故事大会"选项）
    def contextMenuEvent(self, event):
        # 定义右键菜单
        menu = QMenu(self)
        # 定义菜单项：隐藏
        hide = menu.addAction("隐藏")
        # 定义菜单项：休息提醒（根据状态切换文字）
        rest_text = "关闭休息提醒" if self.rest_open == 2 else "打开休息提醒"
        rest_anhour = menu.addAction(rest_text)
        # 分隔线
        menu.addSeparator()
        # 定义菜单项：退出
        quitAction = menu.addAction("退出")

        # 显示菜单并获取点击动作
        action = menu.exec_(self.mapToGlobal(event.pos()))

        # 点击"退出"
        if action == quitAction:
            self.quit()
        # 点击"隐藏"（通过透明度实现）
        elif action == hide:
            self.setWindowOpacity(0)
        # 点击"休息提醒"（切换开关状态）
        elif action == rest_anhour:
            if self.rest_open == 1:
                # 打开休息提醒（1小时一次，3600000毫秒）
                self.timer_rest.start(3600000)
                self.rest_open = 2
                self.tray_icon.showMessage("提醒", "已开启每小时休息提醒～", QSystemTrayIcon.Information, 1500)
            elif self.rest_open == 2:
                # 关闭休息提醒
                self.timer_rest.stop()
                self.rest_open = 1
                self.show_time_rest.setText("")
                self.tray_icon.showMessage("提醒", "已关闭休息提醒～", QSystemTrayIcon.Information, 1500)

    # 休息时间提醒逻辑
    def haveRest(self):
        # 显示休息提示文字
        self.show_time_rest.setText("休息一下吧～")
        self.show_time_rest.adjustSize()

        # 切换宠物状态为休息提醒
        self.condition = 2
        self.randomAct()

        # 将宠物移动到屏幕中央
        screen_geo = QGuiApplication.primaryScreen().geometry()
        pet_geo = self.geometry()
        center_x = (screen_geo.width() - pet_geo.width()) // 2
        center_y = (screen_geo.height() - pet_geo.height()) // 2
        self.move(center_x, center_y)

        # 确保窗口置顶，让用户看到提醒
        self.raise_()
        # 5秒后清除休息提示文字
        QTimer.singleShot(5000, lambda: self.show_time_rest.setText(""))


if __name__ == '__main__':
    # 解决PyQt中文显示问题
    QTextCodec.setCodecForLocale(QTextCodec.codecForName("UTF-8"))
    # 创建应用实例
    app = QApplication(sys.argv)
    # 关闭主窗口后不退出程序（确保托盘继续运行）
    app.setQuitOnLastWindowClosed(False)
    # 初始化桌面宠物
    pet = DesktopPet()
    # 进入事件循环
    sys.exit(app.exec_())