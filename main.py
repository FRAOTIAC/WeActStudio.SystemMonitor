#!/usr/bin/env python3
"""Simple, clean system monitor for WeAct Studio displays.

No async, no over-engineering. Just clean, readable code.
"""

import atexit
import logging
import signal
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

# Check Python version
if sys.version_info < (3, 9):
    raise RuntimeError("Python 3.9+ required")

try:
    import filelock
except ImportError:
    print("Missing dependency: pip install filelock")
    sys.exit(1)


@dataclass
class Config:
    """Simple configuration with sensible defaults."""
    scheduler_stagger_delay: float = 0.15
    health_check_interval: float = 2.0
    reconnect_wait: float = 3.0
    max_reconnect_attempts: int = 20


class DisplayManager:
    """Manages display lifecycle."""
    
    def __init__(self, display, config, logger: logging.Logger):
        self.display = display
        self.config = config
        self.logger = logger
        self.reconnect_attempts = 0
        
    def initialize(self, scheduler_mgr) -> None:
        """Initialize display and show static content."""
        self.logger.info("Initializing display")
        
        self.display.initialize_display()
        self.display.initialize_sensor()
        
        # Start queue handler through scheduler manager
        scheduler_mgr.start_queue_handler()
        
        self.display.display_static_images()
        self.display.display_static_text()
        
        self._wait_for_queue()
        
    def _wait_for_queue(self, timeout: float = 10.0) -> None:
        """Wait for display queue to empty."""
        elapsed = 0.0
        while not self.config.update_queue.empty() and elapsed < timeout:
            time.sleep(0.1)
            elapsed += 0.1
            
    def shutdown(self, scheduler_mgr) -> None:
        """Clean shutdown."""
        self.logger.info("Shutting down display")
        
        self.display.turn_off()
        scheduler_mgr.stop_all()
        self._wait_for_queue(timeout=5.0)
        
        # Brief pause to let daemon threads finish current cycle
        time.sleep(0.5)
        
    def check_health(self, config: Config) -> bool:
        """Check serial connection health.
        
        Returns:
            True if reconnection needed and successful, False to continue
        """
        if self.display.is_LcdSimulated:
            return False
            
        if not self._is_connected():
            return self._try_reconnect(config)
        
        self.reconnect_attempts = 0
        return False
        
    def _is_connected(self) -> bool:
        """Check if serial is open."""
        return (self.display.lcd.lcd_serial and 
                self.display.lcd.lcd_serial.is_open)
                
    def _try_reconnect(self, config: Config) -> bool:
        """Try to reconnect serial.
        
        Returns:
            True if should restart, False if failed
        """
        self.logger.warning("Serial disconnected")
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts > config.max_reconnect_attempts:
            self.logger.error("Max reconnect attempts reached")
            raise RuntimeError("Serial connection lost")
            
        time.sleep(config.reconnect_wait)
        
        try:
            self.display.lcd.lcd_serial.open()
            self.logger.info("Reconnected successfully")
            self.reconnect_attempts = 0
            return True  # Signal to restart
        except Exception as e:
            self.logger.error(f"Reconnect failed: {e}")
            return False


class SchedulerManager:
    """Manages scheduled sensor tasks using modern MetricCollector."""
    
    def __init__(self, config_module, stats, logger: logging.Logger):
        from library.metric_collector import (
            MetricCollector,
            create_default_config_from_theme
        )
        
        self.config_module = config_module
        self.stats = stats
        self.logger = logger
        self.queue_handler_thread = None
        self._stopping = False
        
        # Create collector config from theme
        collector_config = create_default_config_from_theme(
            config_module.THEME_DATA
        )
        self.collector = MetricCollector(collector_config, logger)
        self._register_handlers(stats)
        
    def _register_handlers(self, stats):
        """Register all metric collection handlers."""
        handlers = {
            'cpu_percentage': stats.CPU.percentage,
            'cpu_frequency': stats.CPU.frequency,
            'cpu_load': stats.CPU.load,
            'cpu_temperature': stats.CPU.temperature,
            'cpu_fan_speed': stats.CPU.fan_speed,
            'gpu_stats': stats.Gpu.stats,
            'memory_stats': stats.Memory.stats,
            'disk_stats': stats.Disk.stats,
            'net_stats': stats.Net.stats,
            'weather_stats': stats.Weather.stats,
        }
        
        for task_name, handler in handlers.items():
            self.collector.register_task_handler(task_name, handler)
    
    def start_queue_handler(self) -> None:
        """Start the serial queue handler."""
        def queue_handler_loop():
            """Process serial queue."""
            while not self._stopping:
                try:
                    if not self.config_module.update_queue.empty():
                        f, args = self.config_module.update_queue.get(timeout=0.001)
                        if f:
                            f(*args)
                except:
                    pass
                time.sleep(0.001)  # 1ms polling
        
        self.queue_handler_thread = threading.Thread(
            target=queue_handler_loop,
            name="Queue_Handler",
            daemon=True
        )
        self.queue_handler_thread.start()
        self.logger.debug("Queue handler started")
        
    def start_all(self, stagger_delay: float = None) -> None:
        """Start all monitoring tasks."""
        self.logger.info("Starting metric collector")
        self.collector.start()
    
    def stop_all(self) -> None:
        """Stop all metric collection."""
        self.logger.info("Stopping schedulers")
        self._stopping = True
        self.collector.stop(wait=True, timeout=5.0)
        
        # Wait briefly for queue handler to stop
        if self.queue_handler_thread:
            time.sleep(0.1)


class SystemMonitor:
    """Main monitor application."""
    
    def __init__(self, config: Config):
        self.config = config
        self._stopping = False
        self._setup()
        
    def _setup(self) -> None:
        """Setup logging and load modules."""
        from library.log import logger
        from library.display import display
        from library import stats, config
        
        self.logger = logger
        self.display_mgr = DisplayManager(display, config, logger)
        self.scheduler_mgr = SchedulerManager(config, stats, logger)
        
    def _register_signals(self) -> None:
        """Register signal handlers."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        if hasattr(signal, 'SIGQUIT'):
            signal.signal(signal.SIGQUIT, self._signal_handler)
            
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}")
        self._stopping = True
        
    def run(self) -> None:
        """Main run loop."""
        try:
            self.logger.info("Starting system monitor")
            self._register_signals()
            
            # Initialize
            self.display_mgr.initialize(self.scheduler_mgr)
            self.scheduler_mgr.start_all(self.config.scheduler_stagger_delay)
            
            self.logger.info("Initialization complete, entering main loop")
            
            # Main monitoring loop
            while not self._stopping:
                time.sleep(self.config.health_check_interval)
                
                # Check health and reconnect if needed
                try:
                    if self.display_mgr.check_health(self.config):
                        # Reconnection successful, need to restart
                        self.logger.info("Restarting after reconnection")
                        self.display_mgr.shutdown(self.scheduler_mgr)
                        # In production, external process manager should restart
                        break
                        
                except RuntimeError as e:
                    self.logger.error(f"Fatal error: {e}")
                    break
                    
            # Cleanup
            self.display_mgr.shutdown(self.scheduler_mgr)
            self.logger.info("Shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            raise
            

def main() -> None:
    """Application entry point."""
    # Single instance lock
    lockfile = Path(__file__).with_suffix('.lock')
    lock = filelock.FileLock(lockfile, timeout=1)
    
    try:
        lock.acquire()
        
        # Run monitor
        config = Config()
        monitor = SystemMonitor(config)
        monitor.run()
        
    except filelock.Timeout:
        print("Error: Another instance is already running")
        sys.exit(1)
    finally:
        try:
            lock.release()
        except:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

