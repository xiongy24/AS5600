import serial
import matplotlib.pyplot as plt
import numpy as np
import time
from matplotlib import font_manager
import serial.tools.list_ports
import threading
import queue

def list_com_ports():
    """列出所有可用的COM口"""
    ports = list(serial.tools.list_ports.comports())
    print("\n可用的COM口:")
    for port in ports:
        print(f"- {port.device}: {port.description}")
    return ports

class AngleVisualizer:
    def __init__(self, port='COM4', baudrate=115200):
        # 设置中文字体
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
        except Exception as e:
            print(f"字体设置错误: {e}")
            
        # 初始化数据队列
        self.data_queue = queue.Queue()
        self.running = True
            
        # 初始化串口
        print(f"\n尝试连接串口 {port}...")
        try:
            available_ports = [p.device for p in serial.tools.list_ports.comports()]
            if port not in available_ports:
                print(f"错误: 找不到串口 {port}")
                print("可用的串口:")
                for p in available_ports:
                    print(f"- {p}")
                raise serial.SerialException(f"串口 {port} 不存在")

            self.ser = serial.Serial(port, baudrate, timeout=1)
            print(f"串口连接成功: {port}")
            time.sleep(2)
            
        except Exception as e:
            print(f"串口初始化失败: {e}")
            input("按回车键退出...")
            raise

        print("\n初始化图形界面...")
        try:
            # 创建图形窗口
            self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 5))
            self.ax1 = plt.subplot(121, projection='polar')
            self.ax2 = plt.subplot(122)
            
            self.fig.suptitle('AS5600角度传感器数据可视化')
            self.ax1.set_title('角度表盘')
            self.ax2.set_title('角度时间序列')
            
            # 初始化数据
            self.angle_history = [0]
            self.max_history = 100
            
            # 创建图形元素
            self.line, = self.ax1.plot([0, 0], [0, 1], 'r-', lw=2)
            self.time_line, = self.ax2.plot([], [], 'b-')
            self.text = self.ax2.text(0.02, 1.1, '当前角度: 0.0°', 
                                    transform=self.ax2.transAxes)
            
            # 设置图形属性
            self.ax1.set_rticks([])
            self.ax1.set_rlim(0, 1)
            self.ax1.set_thetagrids(np.arange(0, 360, 30))
            
            self.ax2.set_xlabel('采样点')
            self.ax2.set_ylabel('角度 (°)')
            self.ax2.grid(True)
            self.ax2.set_xlim(0, self.max_history)
            self.ax2.set_ylim(-10, 370)
            
            plt.tight_layout()
            self.fig.canvas.draw()
            print("图形界面初始化完成")
            
        except Exception as e:
            print(f"图形界面初始化失败: {e}")
            if hasattr(self, 'ser'):
                self.ser.close()
            input("按回车键退出...")
            raise

    def read_serial(self):
        """在单独的线程中读取串口数据"""
        while self.running:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode().strip()
                    if 'Degrees:' in line:
                        angle = float(line.split('Degrees:')[1].strip())
                        self.data_queue.put(angle)
            except Exception as e:
                print(f"串口读取错误: {e}")
                break
            time.sleep(0.01)

    def update_plot(self):
        """更新图形"""
        while not self.data_queue.empty():
            try:
                angle = self.data_queue.get_nowait()
                
                # 更新历史数据
                self.angle_history.append(angle)
                if len(self.angle_history) > self.max_history:
                    self.angle_history.pop(0)
                
                # 更新图形
                angle_rad = np.radians(angle)
                self.line.set_data([angle_rad, angle_rad], [0, 1])
                self.time_line.set_data(range(len(self.angle_history)), 
                                      self.angle_history)
                self.text.set_text(f'当前角度: {angle:.1f}°')
                
            except Exception as e:
                print(f"图形更新错误: {e}")
        
        self.fig.canvas.draw_idle()
        return True

    def run(self):
        print("\n开始运行...")
        try:
            # 启动串口读取线程
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.serial_thread.daemon = True
            self.serial_thread.start()
            
            # 设置定时器更新图形
            self.timer = self.fig.canvas.new_timer(interval=50)
            self.timer.add_callback(self.update_plot)
            self.timer.start()
            
            plt.show()
            
        except Exception as e:
            print(f"运行错误: {e}")
        finally:
            self.close()

    def close(self):
        print("\n正在关闭程序...")
        self.running = False
        try:
            if hasattr(self, 'ser') and self.ser.is_open:
                self.ser.close()
                print("串口已关闭")
            if hasattr(self, 'timer'):
                self.timer.stop()
            plt.close('all')
            print("窗口已关闭")
        except Exception as e:
            print(f"关闭错误: {e}")

if __name__ == "__main__":
    print("AS5600角度可视化程序启动...")
    print("按Ctrl+C可以退出程序")
    
    list_com_ports()
    port = input("\n请输入要使用的COM口 (直接回车默认使用COM4): ").strip() or 'COM4'
    
    try:
        visualizer = AngleVisualizer(port=port)
        visualizer.run()
    except KeyboardInterrupt:
        print("\n检测到Ctrl+C，正在退出...")
        if 'visualizer' in locals():
            visualizer.close()
    except Exception as e:
        print(f"\n程序发生错误: {e}")
    finally:
        print("\n程序已终止")
        input("按回车键退出...") 