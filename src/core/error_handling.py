#!/usr/bin/env python3
"""
Centralized error handling and recovery mechanisms for the snooker detection system
"""

import logging
import time
import traceback
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issues, system continues normally
    MEDIUM = "medium"     # Moderate issues, degraded performance
    HIGH = "high"         # Serious issues, major functionality affected
    CRITICAL = "critical" # System-breaking issues, immediate attention required

class ErrorCategory(Enum):
    """Error categories for classification"""
    DETECTION = "detection"
    CALIBRATION = "calibration"
    TRACKING = "tracking"
    VIDEO_INPUT = "video_input"
    MODEL_LOADING = "model_loading"
    DATA_PROCESSING = "data_processing"
    SYSTEM = "system"
    NETWORK = "network"
    STORAGE = "storage"

@dataclass
class ErrorEvent:
    """Represents an error event in the system"""
    timestamp: float
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_strategy: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return {
            "timestamp": self.timestamp,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "exception_type": type(self.exception).__name__ if self.exception else None,
            "exception_message": str(self.exception) if self.exception else None,
            "context": self.context,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "recovery_strategy": self.recovery_strategy
        }

class RecoveryStrategy:
    """Base class for recovery strategies"""
    
    def __init__(self, name: str, max_attempts: int = 3):
        self.name = name
        self.max_attempts = max_attempts
        self.attempt_count = 0
        self.last_attempt_time = 0
        self.cooldown_period = 5.0  # seconds
    
    def can_attempt(self) -> bool:
        """Check if recovery can be attempted"""
        if self.attempt_count >= self.max_attempts:
            return False
        
        # Check cooldown period
        if time.time() - self.last_attempt_time < self.cooldown_period:
            return False
        
        return True
    
    def attempt_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Attempt recovery - to be implemented by subclasses"""
        if not self.can_attempt():
            return False
        
        self.attempt_count += 1
        self.last_attempt_time = time.time()
        
        try:
            return self._execute_recovery(error_event, context)
        except Exception as e:
            logger.error(f"Recovery strategy '{self.name}' failed: {e}")
            return False
    
    def _execute_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Execute the actual recovery logic - to be implemented by subclasses"""
        raise NotImplementedError
    
    def reset(self) -> None:
        """Reset recovery strategy state"""
        self.attempt_count = 0
        self.last_attempt_time = 0

class ErrorHandler:
    """Centralized error handling and recovery system"""
    
    def __init__(self, max_error_history: int = 1000):
        self.max_error_history = max_error_history
        self.error_history: deque = deque(maxlen=max_error_history)
        self.error_counts: Dict[ErrorCategory, int] = defaultdict(int)
        self.recovery_strategies: Dict[ErrorCategory, List[RecoveryStrategy]] = defaultdict(list)
        self.error_callbacks: List[Callable[[ErrorEvent], None]] = []
        
        # Error rate tracking
        self.error_rate_window = 60  # seconds
        self.error_rate_threshold = 10  # errors per minute
        
        # System health monitoring
        self.system_health = {
            "overall_status": "healthy",
            "component_status": {},
            "last_health_check": time.time(),
            "degraded_components": set()
        }
    
    def register_recovery_strategy(self, category: ErrorCategory, strategy: RecoveryStrategy) -> None:
        """Register a recovery strategy for a specific error category"""
        self.recovery_strategies[category].append(strategy)
        logger.info(f"Registered recovery strategy '{strategy.name}' for {category.value} errors")
    
    def register_error_callback(self, callback: Callable[[ErrorEvent], None]) -> None:
        """Register callback to be called when errors occur"""
        self.error_callbacks.append(callback)
    
    def handle_error(self, category: ErrorCategory, severity: ErrorSeverity, 
                    message: str, exception: Optional[Exception] = None,
                    context: Optional[Dict[str, Any]] = None,
                    attempt_recovery: bool = True) -> bool:
        """Handle an error event and attempt recovery if configured"""
        
        # Create error event
        error_event = ErrorEvent(
            timestamp=time.time(),
            category=category,
            severity=severity,
            message=message,
            exception=exception,
            context=context or {}
        )
        
        # Log the error
        self._log_error(error_event)
        
        # Update statistics
        self.error_counts[category] += 1
        self.error_history.append(error_event)
        
        # Check error rate
        self._check_error_rate()
        
        # Update system health
        self._update_system_health(error_event)
        
        # Attempt recovery if enabled and strategies are available
        recovery_successful = False
        if attempt_recovery and category in self.recovery_strategies:
            recovery_successful = self._attempt_recovery(error_event)
        
        # Notify callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_event)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")
        
        return recovery_successful
    
    def _log_error(self, error_event: ErrorEvent) -> None:
        """Log error event with appropriate level"""
        log_message = f"[{error_event.category.value.upper()}] {error_event.message}"
        
        if error_event.context:
            context_str = ", ".join([f"{k}={v}" for k, v in error_event.context.items()])
            log_message += f" | Context: {context_str}"
        
        if error_event.exception:
            log_message += f" | Exception: {error_event.exception}"
        
        # Log based on severity
        if error_event.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
            if error_event.exception:
                logger.critical(traceback.format_exc())
        elif error_event.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_event.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:  # LOW
            logger.info(log_message)
    
    def _attempt_recovery(self, error_event: ErrorEvent) -> bool:
        """Attempt recovery using registered strategies"""
        strategies = self.recovery_strategies[error_event.category]
        
        for strategy in strategies:
            if strategy.can_attempt():
                logger.info(f"Attempting recovery using strategy: {strategy.name}")
                
                error_event.recovery_attempted = True
                error_event.recovery_strategy = strategy.name
                
                success = strategy.attempt_recovery(error_event, error_event.context)
                
                if success:
                    error_event.recovery_successful = True
                    logger.info(f"Recovery successful using strategy: {strategy.name}")
                    return True
                else:
                    logger.warning(f"Recovery failed using strategy: {strategy.name}")
        
        logger.warning(f"All recovery strategies exhausted for {error_event.category.value} error")
        return False
    
    def _check_error_rate(self) -> None:
        """Check if error rate exceeds threshold"""
        current_time = time.time()
        recent_errors = [
            event for event in self.error_history
            if current_time - event.timestamp <= self.error_rate_window
        ]
        
        error_rate = len(recent_errors) / (self.error_rate_window / 60)  # errors per minute
        
        if error_rate > self.error_rate_threshold:
            logger.warning(f"High error rate detected: {error_rate:.1f} errors/min")
            self.system_health["overall_status"] = "degraded"
    
    def _update_system_health(self, error_event: ErrorEvent) -> None:
        """Update system health based on error event"""
        component = error_event.category.value
        
        # Mark component as degraded for high/critical errors
        if error_event.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.system_health["degraded_components"].add(component)
            self.system_health["component_status"][component] = "degraded"
        
        # Update overall status
        if self.system_health["degraded_components"]:
            if any(self._get_recent_errors(cat, 60) > 5 for cat in ErrorCategory):
                self.system_health["overall_status"] = "critical"
            else:
                self.system_health["overall_status"] = "degraded"
        
        self.system_health["last_health_check"] = time.time()
    
    def _get_recent_errors(self, category: ErrorCategory, window_seconds: int) -> int:
        """Get count of recent errors for a category"""
        current_time = time.time()
        return sum(
            1 for event in self.error_history
            if (event.category == category and 
                current_time - event.timestamp <= window_seconds)
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        current_time = time.time()
        
        # Recent error counts (last hour)
        recent_errors = [
            event for event in self.error_history
            if current_time - event.timestamp <= 3600
        ]
        
        recent_by_category = defaultdict(int)
        recent_by_severity = defaultdict(int)
        
        for event in recent_errors:
            recent_by_category[event.category.value] += 1
            recent_by_severity[event.severity.value] += 1
        
        # Recovery success rate
        recovery_attempts = [e for e in self.error_history if e.recovery_attempted]
        recovery_success_rate = 0.0
        if recovery_attempts:
            successful_recoveries = [e for e in recovery_attempts if e.recovery_successful]
            recovery_success_rate = len(successful_recoveries) / len(recovery_attempts)
        
        return {
            "total_errors": len(self.error_history),
            "error_counts_by_category": dict(self.error_counts),
            "recent_errors_by_category": dict(recent_by_category),
            "recent_errors_by_severity": dict(recent_by_severity),
            "recovery_success_rate": recovery_success_rate,
            "system_health": self.system_health.copy(),
            "error_rate_last_hour": len(recent_errors) / 60,  # per minute
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error events"""
        recent = list(self.error_history)[-limit:]
        return [event.to_dict() for event in recent]
    
    def reset_error_statistics(self) -> None:
        """Reset all error statistics"""
        self.error_history.clear()
        self.error_counts.clear()
        
        # Reset recovery strategies
        for strategies in self.recovery_strategies.values():
            for strategy in strategies:
                strategy.reset()
        
        # Reset system health
        self.system_health = {
            "overall_status": "healthy",
            "component_status": {},
            "last_health_check": time.time(),
            "degraded_components": set()
        }
        
        logger.info("Error statistics reset")
    
    def is_system_healthy(self) -> bool:
        """Check if system is in healthy state"""
        return self.system_health["overall_status"] == "healthy"
    
    def get_degraded_components(self) -> List[str]:
        """Get list of degraded components"""
        return list(self.system_health["degraded_components"])


# Global error handler instance
global_error_handler = ErrorHandler()

def handle_error(category: ErrorCategory, severity: ErrorSeverity, 
                message: str, exception: Optional[Exception] = None,
                context: Optional[Dict[str, Any]] = None,
                attempt_recovery: bool = True) -> bool:
    """Convenience function to handle errors using global handler"""
    return global_error_handler.handle_error(
        category, severity, message, exception, context, attempt_recovery
    )