"""Metric Collector - Modern task scheduling for system monitoring.

Replaces the old scheduler.py with:
- Pydantic for configuration validation
- APScheduler for efficient task scheduling  
- Type safety and configuration-driven design
"""

import logging
from enum import Enum
from typing import Callable, Optional

from pydantic import BaseModel, Field, field_validator

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    print("[WARNING] APScheduler not available. Install: pip install apscheduler")


class MetricType(str, Enum):
    """Types of metrics that can be collected."""
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    SENSOR = "sensor"
    WEATHER = "weather"
    CUSTOM = "custom"


class MetricTaskConfig(BaseModel):
    """Configuration for a single metric collection task.
    
    Example:
        >>> task = MetricTaskConfig(
        ...     name="cpu_percentage",
        ...     metric_type=MetricType.CPU,
        ...     interval_seconds=1.0,
        ...     enabled=True
        ... )
    """
    name: str = Field(
        description="Unique identifier for this task"
    )
    metric_type: MetricType = Field(
        description="Type of metric being collected"
    )
    interval_seconds: float = Field(
        gt=0.0,
        description="How often to collect this metric (seconds)"
    )
    enabled: bool = Field(
        default=True,
        description="Whether this task is active"
    )
    max_instances: int = Field(
        default=1,
        ge=1,
        description="Maximum concurrent instances of this task"
    )
    
    @field_validator('interval_seconds')
    @classmethod
    def validate_interval(cls, v: float) -> float:
        """Ensure interval is reasonable."""
        if v < 0.1:
            raise ValueError("Interval too short, minimum 0.1 seconds")
        if v > 86400:  # 24 hours
            raise ValueError("Interval too long, maximum 86400 seconds")
        return v


class MetricCollectorConfig(BaseModel):
    """Configuration for the entire metric collector.
    
    Example:
        >>> config = MetricCollectorConfig(
        ...     max_workers=4,
        ...     tasks=[
        ...         MetricTaskConfig(name="cpu", metric_type=MetricType.CPU, interval_seconds=1.0),
        ...         MetricTaskConfig(name="memory", metric_type=MetricType.MEMORY, interval_seconds=3.0),
        ...     ]
        ... )
    """
    max_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum worker threads for task execution"
    )
    tasks: list[MetricTaskConfig] = Field(
        default_factory=list,
        description="List of metric collection tasks"
    )
    
    @field_validator('tasks')
    @classmethod
    def validate_unique_names(cls, v: list[MetricTaskConfig]) -> list[MetricTaskConfig]:
        """Ensure all task names are unique."""
        names = [task.name for task in v]
        if len(names) != len(set(names)):
            raise ValueError("Task names must be unique")
        return v


class MetricCollector:
    """Modern metric collector using APScheduler.
    
    Replaces the old threading-based scheduler with a more efficient
    and maintainable solution.
    
    Example:
        >>> collector = MetricCollector(config)
        >>> collector.register_task_handler('cpu_percentage', stats.CPU.percentage)
        >>> collector.start()
        >>> # ... later
        >>> collector.stop()
    """
    
    def __init__(
        self, 
        config: MetricCollectorConfig,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the metric collector.
        
        Args:
            config: Configuration for tasks and scheduler
            logger: Logger instance (creates one if not provided)
        """
        if not APSCHEDULER_AVAILABLE:
            raise RuntimeError(
                "APScheduler is required. Install: pip install apscheduler"
            )
            
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.task_handlers: dict[str, Callable] = {}
        
        # Create scheduler with daemon threads
        self.scheduler = BackgroundScheduler(
            daemon=True,
            max_workers=config.max_workers
        )
        
    def register_task_handler(self, task_name: str, handler: Callable) -> None:
        """Register a function to handle a specific task.
        
        Args:
            task_name: Name of the task (must match config)
            handler: Function to call for this task
            
        Example:
            >>> collector.register_task_handler('cpu_percentage', stats.CPU.percentage)
        """
        self.task_handlers[task_name] = handler
        self.logger.debug(f"Registered handler for task: {task_name}")
        
    def start(self) -> None:
        """Start collecting metrics according to configuration."""
        if not self.task_handlers:
            self.logger.warning("No task handlers registered")
            return
            
        self.logger.info(f"Starting metric collector with {len(self.config.tasks)} tasks")
        
        for task_config in self.config.tasks:
            if not task_config.enabled:
                self.logger.debug(f"Skipping disabled task: {task_config.name}")
                continue
                
            if task_config.name not in self.task_handlers:
                self.logger.warning(
                    f"No handler registered for task: {task_config.name}"
                )
                continue
                
            handler = self.task_handlers[task_config.name]
            
            self.scheduler.add_job(
                func=handler,
                trigger=IntervalTrigger(seconds=task_config.interval_seconds),
                id=task_config.name,
                name=f"{task_config.metric_type.value}: {task_config.name}",
                max_instances=task_config.max_instances,
                replace_existing=True
            )
            
            self.logger.info(
                f"Scheduled task '{task_config.name}' "
                f"(interval: {task_config.interval_seconds}s)"
            )
        
        self.scheduler.start()
        self.logger.info("Metric collector started")
        
    def stop(self, wait: bool = True, timeout: float = 5.0) -> None:
        """Stop collecting metrics.
        
        Args:
            wait: Whether to wait for running jobs to complete
            timeout: Maximum seconds to wait
        """
        self.logger.info("Stopping metric collector")
        self.scheduler.shutdown(wait=wait, timeout=timeout)
        self.logger.info("Metric collector stopped")
        
    def pause_task(self, task_name: str) -> None:
        """Pause a specific task."""
        self.scheduler.pause_job(task_name)
        self.logger.info(f"Paused task: {task_name}")
        
    def resume_task(self, task_name: str) -> None:
        """Resume a paused task."""
        self.scheduler.resume_job(task_name)
        self.logger.info(f"Resumed task: {task_name}")
        
    def get_status(self) -> dict:
        """Get current status of all tasks."""
        jobs = self.scheduler.get_jobs()
        return {
            'running': self.scheduler.running,
            'task_count': len(jobs),
            'tasks': [
                {
                    'name': job.id,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                }
                for job in jobs
            ]
        }


def create_default_config_from_theme(theme_data: dict) -> MetricCollectorConfig:
    """Create metric collector config from theme configuration.
    
    This is a bridge function to maintain compatibility with the existing
    config.THEME_DATA structure.
    
    Args:
        theme_data: Dictionary from config.THEME_DATA
        
    Returns:
        MetricCollectorConfig with tasks extracted from theme
    """
    tasks = []
    stats_config = theme_data.get('STATS', {})
    
    # CPU metrics
    cpu_config = stats_config.get('CPU', {})
    if cpu_config.get('PERCENTAGE', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='cpu_percentage',
            metric_type=MetricType.CPU,
            interval_seconds=cpu_config['PERCENTAGE']['INTERVAL']
        ))
    
    if cpu_config.get('FREQUENCY', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='cpu_frequency',
            metric_type=MetricType.CPU,
            interval_seconds=cpu_config['FREQUENCY']['INTERVAL']
        ))
    
    if cpu_config.get('LOAD', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='cpu_load',
            metric_type=MetricType.CPU,
            interval_seconds=cpu_config['LOAD']['INTERVAL']
        ))
    
    if cpu_config.get('TEMPERATURE', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='cpu_temperature',
            metric_type=MetricType.CPU,
            interval_seconds=cpu_config['TEMPERATURE']['INTERVAL']
        ))
    
    if cpu_config.get('FAN_SPEED', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='cpu_fan_speed',
            metric_type=MetricType.CPU,
            interval_seconds=cpu_config['FAN_SPEED']['INTERVAL']
        ))
    
    # GPU metrics
    if stats_config.get('GPU', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='gpu_stats',
            metric_type=MetricType.GPU,
            interval_seconds=stats_config['GPU']['INTERVAL']
        ))
    
    # Memory metrics
    if stats_config.get('MEMORY', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='memory_stats',
            metric_type=MetricType.MEMORY,
            interval_seconds=stats_config['MEMORY']['INTERVAL']
        ))
    
    # Disk metrics
    if stats_config.get('DISK', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='disk_stats',
            metric_type=MetricType.DISK,
            interval_seconds=stats_config['DISK']['INTERVAL']
        ))
    
    # Network metrics
    if stats_config.get('NET', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='net_stats',
            metric_type=MetricType.NETWORK,
            interval_seconds=stats_config['NET']['INTERVAL']
        ))
    
    # Weather metrics
    if stats_config.get('WEATHER', {}).get('INTERVAL', 0) > 0:
        tasks.append(MetricTaskConfig(
            name='weather_stats',
            metric_type=MetricType.WEATHER,
            interval_seconds=max(300.0, stats_config['WEATHER']['INTERVAL'])
        ))
    
    return MetricCollectorConfig(
        max_workers=4,
        tasks=tasks
    )

