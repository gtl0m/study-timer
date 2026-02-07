import os
import sys
import time
import msvcrt
import winsound

# --- 配置与常量 ---
CONFIG_FILE = "subjects.txt"

# ANSI 颜色代码 (Windows 10/11 终端支持)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# 旋转动画符号
SPINNER_CHARS = ['|', '/', '-', '\\']

# --- 辅助函数 ---

def clear_screen():
    """清屏"""
    os.system('cls')

def play_sound(times=1):
    """播放提示音 (系统默认提示音)"""
    try:
        for _ in range(times):
            # Windows 默认提示音
            winsound.MessageBeep()
            time.sleep(0.2)
    except:
        pass

def create_default_config():
    """如果配置文件不存在，创建默认配置"""
    if not os.path.exists(CONFIG_FILE):
        default_content = "数学:60\n英语:45\n编程:90\n阅读:30"
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(default_content)

def load_config():
    """读取配置文件"""
    subjects = []
    create_default_config()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(':')
                if len(parts) == 2:
                    name = parts[0].strip()
                    try:
                        duration = int(parts[1].strip())
                        subjects.append({'name': name, 'duration': duration})
                    except ValueError:
                        continue
    except Exception as e:
        print(f"{Colors.RED}读取配置文件出错: {e}{Colors.ENDC}")
        time.sleep(2)
    return subjects

def format_time(seconds):
    """将秒转换为 MM:SS 格式"""
    if seconds < 0: seconds = 0
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

# --- 核心程序类 ---

class StudyApp:
    def __init__(self):
        self.subjects = load_config()
        self.running = True
        self.current_state = "MENU" # MENU, STUDY, BREAK_SELECT, BREAK, POST_BREAK
        
        # 学习相关变量
        self.current_subject = ""
        self.remaining_study_time = 0
        self.study_paused = False
        
        # 休息相关变量
        self.remaining_break_time = 0

    def get_input(self):
        """非阻塞获取键盘输入"""
        if msvcrt.kbhit():
            try:
                # 获取按键并解码
                key = msvcrt.getch()
                return key.decode('utf-8').lower()
            except UnicodeDecodeError:
                return None
        return None

    def run(self):
        while self.running:
            if self.current_state == "MENU":
                self.menu_loop()
            elif self.current_state == "STUDY":
                self.study_loop()
            elif self.current_state == "BREAK_SELECT":
                self.break_select_loop()
            elif self.current_state == "BREAK":
                self.break_loop()
            elif self.current_state == "POST_BREAK":
                self.post_break_loop()

    def menu_loop(self):
        """主菜单循环"""
        clear_screen()
        print(f"{Colors.HEADER}========================================{Colors.ENDC}")
        print(f"{Colors.HEADER}       📚 学习倒计时管理器 v1.3       {Colors.ENDC}")
        print(f"{Colors.HEADER}========================================{Colors.ENDC}")
        print(f"{Colors.YELLOW}按 's' 退出软件{Colors.ENDC}\n")
        
        if not self.subjects:
            print(f"{Colors.RED}配置文件为空或格式错误！请检查 {CONFIG_FILE}{Colors.ENDC}")
            time.sleep(2)
            self.subjects = load_config()
            return

        print("请选择要学习的学科：")
        for i, sub in enumerate(self.subjects):
            print(f"{Colors.CYAN}[{i+1}] {sub['name']} ({sub['duration']} 分钟){Colors.ENDC}")

        while self.current_state == "MENU":
            key = self.get_input()
            if key == 's':
                self.quit_app()
            elif key and key.isdigit():
                idx = int(key) - 1
                if 0 <= idx < len(self.subjects):
                    selected = self.subjects[idx]
                    self.current_subject = selected['name']
                    self.remaining_study_time = selected['duration'] * 60 
                    self.current_state = "STUDY"
            
            time.sleep(0.1)

    def study_loop(self):
        """学习倒计时循环"""
        clear_screen()
        print(f"{Colors.GREEN}正在学习: {self.current_subject}{Colors.ENDC}")
        print(f"{Colors.YELLOW}控制: [p]暂停/继续  [b]休息  [s]结束软件{Colors.ENDC}")
        print("-" * 50)
        
        last_time = time.time()
        
        # 初始显示一次
        self.print_timer_line()

        while self.current_state == "STUDY":
            current_time = time.time()
            delta = current_time - last_time
            last_time = current_time

            key = self.get_input()
            if key == 's':
                self.quit_app()
            elif key == 'p':
                self.study_paused = not self.study_paused
                last_time = time.time() # 暂停恢复后重置时间锚点
                self.print_timer_line() # 立即刷新状态
            elif key == 'b':
                self.current_state = "BREAK_SELECT"
                return

            if not self.study_paused:
                self.remaining_study_time -= delta
                self.print_timer_line()

                if self.remaining_study_time <= 0:
                    self.finish_study()
                    return
            
            time.sleep(0.1)

    def print_timer_line(self):
        """统一处理倒计时行的打印，使用 \r 覆盖当前行"""
        # padding 用于覆盖可能残留的长字符
        padding = " " * 20 
        
        if self.study_paused:
            status_text = f"{Colors.RED}>> 已暂停 (按 p 继续) <<{Colors.ENDC}"
            sys.stdout.write(f"\r{status_text}{padding}")
        else:
            spinner = SPINNER_CHARS[int(time.time() * 2) % 4]
            time_str = format_time(self.remaining_study_time)
            timer_text = f"{Colors.CYAN}{spinner} 剩余时间: {Colors.BOLD}{time_str}{Colors.ENDC} {Colors.CYAN}{spinner}{Colors.ENDC}"
            sys.stdout.write(f"\r{timer_text}{padding}")
        
        sys.stdout.flush()

    def finish_study(self):
        """学习结束处理：无弹窗，仅声音和文字"""
        clear_screen()
        print(f"\n\n{Colors.HEADER}****************************************{Colors.ENDC}")
        print(f"{Colors.GREEN}       🎉 {self.current_subject} 学习计划完成！       {Colors.ENDC}")
        print(f"{Colors.HEADER}****************************************{Colors.ENDC}")
        
        # 播放提示音 (3声)
        play_sound(3)
        
        print(f"\n{Colors.YELLOW}按任意键返回主菜单...{Colors.ENDC}")
        msvcrt.getch()
        self.current_state = "MENU"

    def break_select_loop(self):
        """休息时长选择"""
        clear_screen()
        print(f"{Colors.BLUE}=== 进入休息模式 ==={Colors.ENDC}")
        print(f"当前学习剩余时间已保存: {format_time(self.remaining_study_time)}")
        print(f"{Colors.YELLOW}请按下数字键 [1-9] 选择休息分钟数{Colors.ENDC}")
        print(f"{Colors.RED}按 [b] 返回学习  |  按 [s] 结束软件{Colors.ENDC}")

        while self.current_state == "BREAK_SELECT":
            key = self.get_input()
            if key == 's':
                self.quit_app()
            elif key == 'b':
                self.current_state = "STUDY"
                return
            elif key and key.isdigit():
                minutes = int(key)
                if 1 <= minutes <= 9:
                    self.remaining_break_time = minutes * 60
                    self.current_state = "BREAK"
            
            time.sleep(0.1)

    def break_loop(self):
        """休息倒计时循环"""
        clear_screen()
        print(f"{Colors.BLUE}☕ 正在休息中...{Colors.ENDC}")
        print(f"{Colors.RED}控制: [b]提前结束休息并返回学习  [s]结束软件{Colors.ENDC}")
        print(f"(注: 休息模式无法暂停)")
        print("-" * 50)

        last_time = time.time()

        while self.current_state == "BREAK":
            current_time = time.time()
            delta = current_time - last_time
            last_time = current_time

            key = self.get_input()
            if key == 's':
                self.quit_app()
            elif key == 'b':
                self.current_state = "STUDY"
                return
            
            self.remaining_break_time -= delta
            
            # 休息动画显示
            spinner = SPINNER_CHARS[int(time.time() * 2) % 4]
            time_str = format_time(self.remaining_break_time)
            padding = " " * 10
            
            sys.stdout.write(f"\r{Colors.YELLOW}{spinner} 休息倒计时: {Colors.BOLD}{time_str}{Colors.ENDC} {Colors.YELLOW}{spinner}{Colors.ENDC}{padding}")
            sys.stdout.flush()

            if self.remaining_break_time <= 0:
                self.finish_break()
                return

            time.sleep(0.1)

    def finish_break(self):
        """休息结束处理：无弹窗，仅声音和文字"""
        clear_screen()
        print(f"\n\n{Colors.BLUE}****************************************{Colors.ENDC}")
        print(f"{Colors.BLUE}          🔔 休息时间结束！          {Colors.ENDC}")
        print(f"{Colors.BLUE}****************************************{Colors.ENDC}")
        
        # 播放提示音 (2声)
        play_sound(2)
        
        self.current_state = "POST_BREAK"

    def post_break_loop(self):
        """休息结束后的等待界面"""
        print(f"\n{Colors.GREEN}>>> 该继续学习了！ <<<{Colors.ENDC}")
        print(f"{Colors.GREEN}>>> 请按 [b] 键继续之前的学习 ({self.current_subject}) <<<{Colors.ENDC}")
        print(f"{Colors.RED}按 [s] 结束软件{Colors.ENDC}")
        
        while self.current_state == "POST_BREAK":
            key = self.get_input()
            if key == 's':
                self.quit_app()
            elif key == 'b':
                self.current_state = "STUDY"
            
            time.sleep(0.1)

    def quit_app(self):
        print(f"\n{Colors.RED}正在退出...{Colors.ENDC}")
        self.running = False
        sys.exit()

if __name__ == "__main__":
    # 初始化 Windows 终端 ANSI 支持
    os.system('') 
    
    app = StudyApp()
    app.run()
