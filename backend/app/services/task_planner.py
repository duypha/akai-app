"""
Task Planner Service - Manages step-by-step task plans for IT support
"""

import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from app.services.database import db


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStatus(Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    """A single step in a task plan"""
    id: str
    plan_id: str
    order: int
    title: str
    description: str
    status: StepStatus = StepStatus.PENDING
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "order": self.order,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


@dataclass
class TaskPlan:
    """A complete task plan with multiple steps"""
    id: str
    session_id: str
    title: str
    description: str
    template_id: Optional[str]
    steps: List[TaskStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.CREATED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    @property
    def progress(self) -> Dict[str, int]:
        """Calculate progress stats"""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in self.steps if s.status == StepStatus.FAILED)
        skipped = sum(1 for s in self.steps if s.status == StepStatus.SKIPPED)
        pending = sum(1 for s in self.steps if s.status == StepStatus.PENDING)
        in_progress = sum(1 for s in self.steps if s.status == StepStatus.IN_PROGRESS)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "pending": pending,
            "in_progress": in_progress,
            "percent": int((completed / total) * 100) if total > 0 else 0
        }

    @property
    def current_step(self) -> Optional[TaskStep]:
        """Get the current active step"""
        for step in self.steps:
            if step.status == StepStatus.IN_PROGRESS:
                return step
        # If no step is in progress, return next pending step
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                return step
        return None

    def to_dict(self, include_steps: bool = True) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "session_id": self.session_id,
            "title": self.title,
            "description": self.description,
            "template_id": self.template_id,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }
        if include_steps:
            result["steps"] = [s.to_dict() for s in self.steps]
        current = self.current_step
        result["current_step"] = current.to_dict() if current else None
        return result


@dataclass
class TaskTemplate:
    """A reusable template for common tasks"""
    id: str
    name: str
    description: str
    category: str
    keywords: List[str]
    steps: List[Dict[str, str]]  # {"title": "...", "description": "..."}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "keywords": self.keywords,
            "steps": self.steps
        }


class TaskPlanner:
    """Task Planner for IT Support - manages step-by-step task plans"""

    def __init__(self):
        self.plans: Dict[str, TaskPlan] = {}
        self.templates: Dict[str, TaskTemplate] = {}
        self._init_default_templates()

    def _init_default_templates(self):
        """Initialize with common IT task templates"""

        self._add_template(
            name="Fix Printer Offline",
            description="Steps to troubleshoot and fix an offline printer",
            category="Printer",
            keywords=["printer", "offline", "not printing", "disconnected"],
            steps=[
                {"title": "Check Physical Connection", "description": "Verify printer is powered on and cables are connected"},
                {"title": "Restart Printer", "description": "Power cycle the printer - turn off, wait 30 seconds, turn on"},
                {"title": "Check Print Queue", "description": "Clear any stuck print jobs from the queue"},
                {"title": "Restart Print Spooler", "description": "Restart the Windows Print Spooler service"},
                {"title": "Set as Default Printer", "description": "Ensure the printer is set as the default"},
                {"title": "Test Print", "description": "Send a test page to verify the fix"}
            ]
        )

        self._add_template(
            name="Clear Print Queue",
            description="Clear stuck print jobs and restart printing",
            category="Printer",
            keywords=["print", "queue", "stuck", "clear", "pending jobs"],
            steps=[
                {"title": "Open Print Queue", "description": "Go to Settings > Printers & scanners > Open queue"},
                {"title": "Cancel All Jobs", "description": "Click Printer menu > Cancel All Documents"},
                {"title": "Stop Print Spooler", "description": "If jobs won't clear, stop the Print Spooler service"},
                {"title": "Clear Spool Folder", "description": "Delete files in C:\\Windows\\System32\\spool\\PRINTERS"},
                {"title": "Restart Print Spooler", "description": "Start the Print Spooler service again"},
                {"title": "Test Print", "description": "Send a test document to verify"}
            ]
        )

        self._add_template(
            name="Fix No Internet",
            description="Troubleshoot and restore internet connectivity",
            category="Network",
            keywords=["internet", "network", "wifi", "connection", "offline", "no internet"],
            steps=[
                {"title": "Check WiFi/Ethernet", "description": "Verify WiFi is enabled or ethernet cable is connected"},
                {"title": "Run Troubleshooter", "description": "Right-click network icon > Troubleshoot problems"},
                {"title": "Restart Router", "description": "Power cycle your router - unplug for 30 seconds"},
                {"title": "Reset Network Adapter", "description": "Run ipconfig /release and ipconfig /renew"},
                {"title": "Flush DNS", "description": "Run ipconfig /flushdns in Command Prompt"},
                {"title": "Test Connection", "description": "Try accessing a website to verify"}
            ]
        )

        self._add_template(
            name="Reset Windows Password",
            description="Help user reset their Windows account password",
            category="Login",
            keywords=["password", "forgot", "reset", "login", "locked out", "can't sign in"],
            steps=[
                {"title": "Access Login Screen", "description": "Get to the Windows login screen"},
                {"title": "Click Reset Password", "description": "Look for 'I forgot my password' or 'Reset password' link"},
                {"title": "Verify Identity", "description": "Answer security questions or verify via email/phone"},
                {"title": "Create New Password", "description": "Enter and confirm the new password"},
                {"title": "Login with New Password", "description": "Use the new password to sign in"},
                {"title": "Update Password Managers", "description": "Update any saved passwords if needed"}
            ]
        )

        self._add_template(
            name="Fix Slow Computer",
            description="Improve computer performance and speed",
            category="Performance",
            keywords=["slow", "performance", "sluggish", "laggy", "freezing", "speed"],
            steps=[
                {"title": "Restart Computer", "description": "Perform a full restart of the computer"},
                {"title": "Check Task Manager", "description": "Open Task Manager and identify high resource usage"},
                {"title": "Close Unnecessary Apps", "description": "End processes using excessive CPU or memory"},
                {"title": "Disable Startup Programs", "description": "Remove unnecessary programs from startup"},
                {"title": "Run Disk Cleanup", "description": "Free up disk space using Disk Cleanup tool"},
                {"title": "Check for Malware", "description": "Run Windows Security or antivirus scan"},
                {"title": "Verify Improvement", "description": "Check if performance has improved"}
            ]
        )

        self._add_template(
            name="Connect External Monitor",
            description="Set up and configure an external monitor or projector",
            category="Display",
            keywords=["monitor", "display", "screen", "projector", "hdmi", "second screen", "external"],
            steps=[
                {"title": "Connect Cable", "description": "Connect HDMI, DisplayPort, or VGA cable to both devices"},
                {"title": "Power On Monitor", "description": "Ensure the external monitor is powered on"},
                {"title": "Open Display Settings", "description": "Press Windows + P or go to Settings > System > Display"},
                {"title": "Detect Display", "description": "Click 'Detect' if monitor doesn't appear automatically"},
                {"title": "Choose Display Mode", "description": "Select Duplicate, Extend, or Second screen only"},
                {"title": "Adjust Resolution", "description": "Set appropriate resolution for the monitor"},
                {"title": "Verify Display", "description": "Confirm both screens are working correctly"}
            ]
        )

        self._add_template(
            name="Fix No Sound",
            description="Troubleshoot and fix audio issues",
            category="Audio",
            keywords=["sound", "audio", "speakers", "no sound", "mute", "volume", "headphones"],
            steps=[
                {"title": "Check Volume", "description": "Click speaker icon and verify volume is not muted"},
                {"title": "Check Output Device", "description": "Right-click speaker > Open Sound settings > Check output device"},
                {"title": "Run Audio Troubleshooter", "description": "Click Troubleshoot in Sound settings"},
                {"title": "Check Physical Connections", "description": "Verify speakers/headphones are properly connected"},
                {"title": "Update Audio Drivers", "description": "Open Device Manager > Update audio drivers"},
                {"title": "Restart Windows Audio", "description": "Restart Windows Audio service if needed"},
                {"title": "Test Audio", "description": "Play a sound to verify the fix"}
            ]
        )

        self._add_template(
            name="Setup Email in Outlook",
            description="Configure a new email account in Microsoft Outlook",
            category="Email",
            keywords=["outlook", "email", "setup", "configure", "add account", "mail"],
            steps=[
                {"title": "Open Outlook", "description": "Launch Microsoft Outlook application"},
                {"title": "Go to Account Settings", "description": "Click File > Add Account"},
                {"title": "Enter Email Address", "description": "Type the email address to add"},
                {"title": "Enter Password", "description": "Provide the email password when prompted"},
                {"title": "Complete Setup", "description": "Follow prompts to finish configuration"},
                {"title": "Send Test Email", "description": "Send a test email to verify setup"}
            ]
        )

        self._add_template(
            name="Repair Office Application",
            description="Fix issues with Microsoft Office applications",
            category="Application",
            keywords=["office", "word", "excel", "outlook", "crash", "repair", "not working"],
            steps=[
                {"title": "Close All Office Apps", "description": "Ensure all Office applications are closed"},
                {"title": "Open Apps Settings", "description": "Go to Settings > Apps > Apps & features"},
                {"title": "Find Microsoft Office", "description": "Search for and select Microsoft Office or 365"},
                {"title": "Click Modify", "description": "Click the Modify button"},
                {"title": "Choose Repair Type", "description": "Select Quick Repair first (or Online Repair if needed)"},
                {"title": "Complete Repair", "description": "Follow prompts and wait for repair to finish"},
                {"title": "Test Application", "description": "Open the Office app to verify it works"}
            ]
        )

        self._add_template(
            name="Fix Bluetooth Device",
            description="Connect or reconnect a Bluetooth device",
            category="Bluetooth",
            keywords=["bluetooth", "wireless", "headphones", "mouse", "keyboard", "pairing"],
            steps=[
                {"title": "Toggle Bluetooth Off", "description": "Turn off Bluetooth in Action Center"},
                {"title": "Wait 10 Seconds", "description": "Give it a moment"},
                {"title": "Toggle Bluetooth On", "description": "Turn Bluetooth back on"},
                {"title": "Put Device in Pairing Mode", "description": "Check device manual for pairing mode"},
                {"title": "Add Device", "description": "Click Add device > Bluetooth"},
                {"title": "Select Your Device", "description": "Choose your device from the list"},
                {"title": "Complete Pairing", "description": "Follow any prompts to finish"}
            ]
        )

        self._add_template(
            name="Clear Browser Cache",
            description="Speed up browser by clearing cache and cookies",
            category="Browser",
            keywords=["browser", "cache", "slow", "chrome", "firefox", "edge", "clear"],
            steps=[
                {"title": "Open Browser Settings", "description": "Press Ctrl+Shift+Delete"},
                {"title": "Select Time Range", "description": "Choose 'All time' from dropdown"},
                {"title": "Select What to Clear", "description": "Check cache and cookies"},
                {"title": "Clear Data", "description": "Click Clear data button"},
                {"title": "Restart Browser", "description": "Close and reopen browser"},
                {"title": "Test Speed", "description": "Browse to verify improvement"}
            ]
        )

        self._add_template(
            name="Free Up Disk Space",
            description="Clear space on a full hard drive",
            category="Storage",
            keywords=["disk", "space", "full", "storage", "clean", "low space"],
            steps=[
                {"title": "Open Disk Cleanup", "description": "Search for Disk Cleanup in Start menu"},
                {"title": "Select Drive", "description": "Choose your main drive (usually C:)"},
                {"title": "Select Files to Delete", "description": "Check all safe options"},
                {"title": "Clean System Files", "description": "Click 'Clean up system files' for more space"},
                {"title": "Empty Recycle Bin", "description": "Right-click Recycle Bin > Empty"},
                {"title": "Clear Temp Files", "description": "Run %temp% and delete contents"},
                {"title": "Verify Space Freed", "description": "Check drive properties for new free space"}
            ]
        )

        self._add_template(
            name="Fix Webcam Issues",
            description="Get your camera working for video calls",
            category="Camera",
            keywords=["camera", "webcam", "video", "zoom", "teams", "not working"],
            steps=[
                {"title": "Check Physical Camera", "description": "Remove any lens cover, check for switch"},
                {"title": "Open Camera Settings", "description": "Go to Settings > Privacy > Camera"},
                {"title": "Enable Camera Access", "description": "Turn on Camera access toggle"},
                {"title": "Enable for Apps", "description": "Turn on access for your meeting app"},
                {"title": "Test in Camera App", "description": "Open Windows Camera app to test"},
                {"title": "Restart Meeting App", "description": "Close and reopen Zoom/Teams"},
                {"title": "Test Video", "description": "Start a test call to verify"}
            ]
        )

        self._add_template(
            name="Fix Windows Update",
            description="Resolve stuck or failed Windows updates",
            category="Updates",
            keywords=["update", "windows update", "stuck", "failed", "installing"],
            steps=[
                {"title": "Run Update Troubleshooter", "description": "Settings > Troubleshoot > Windows Update"},
                {"title": "Restart Computer", "description": "Full restart, not sleep"},
                {"title": "Check Update Status", "description": "Go to Settings > Windows Update"},
                {"title": "Retry Update", "description": "Click Check for updates"},
                {"title": "If Still Stuck", "description": "Note the error code if any"},
                {"title": "Manual Reset if Needed", "description": "May need to reset update components"}
            ]
        )

        self._add_template(
            name="Fix VPN Connection",
            description="Troubleshoot VPN that won't connect",
            category="VPN",
            keywords=["vpn", "connect", "remote", "corporate", "network"],
            steps=[
                {"title": "Check Internet", "description": "Make sure regular internet works"},
                {"title": "Restart VPN App", "description": "Close and reopen VPN application"},
                {"title": "Try Different Server", "description": "Select a different VPN server"},
                {"title": "Check Credentials", "description": "Verify username and password"},
                {"title": "Flush DNS", "description": "Run ipconfig /flushdns in CMD"},
                {"title": "Restart Computer", "description": "Full restart if still not working"},
                {"title": "Contact IT", "description": "May need VPN reconfiguration"}
            ]
        )

    def _add_template(self, name: str, description: str, category: str,
                      keywords: List[str], steps: List[Dict[str, str]]) -> TaskTemplate:
        """Helper to add a template"""
        template_id = str(uuid.uuid4())
        template = TaskTemplate(
            id=template_id,
            name=name,
            description=description,
            category=category,
            keywords=keywords,
            steps=steps
        )
        self.templates[template_id] = template
        return template

    def get_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all templates, optionally filtered by category"""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category.lower() == category.lower()]
        return [t.to_dict() for t in templates]

    def detect_template(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Detect if a message matches a template

        Args:
            message: User's message

        Returns:
            Best matching template or None
        """
        message_lower = message.lower()
        best_match = None
        best_score = 0

        for template in self.templates.values():
            score = 0

            # Check keywords
            for keyword in template.keywords:
                if keyword.lower() in message_lower:
                    score += 3
                # Check individual words
                for word in keyword.lower().split():
                    if len(word) > 2 and word in message_lower:
                        score += 1

            # Check template name
            for word in template.name.lower().split():
                if len(word) > 2 and word in message_lower:
                    score += 2

            if score > best_score:
                best_score = score
                best_match = template

        if best_match and best_score >= 3:  # Minimum threshold
            result = best_match.to_dict()
            result["match_score"] = best_score
            return result

        return None

    def create_plan(self, session_id: str, title: str, description: str,
                    steps: List[Dict[str, str]], template_id: Optional[str] = None) -> TaskPlan:
        """
        Create a new task plan

        Args:
            session_id: ID of the session
            title: Plan title
            description: Plan description
            steps: List of {"title": "...", "description": "..."} dicts
            template_id: Optional template ID if created from template

        Returns:
            Created TaskPlan
        """
        plan_id = str(uuid.uuid4())
        plan = TaskPlan(
            id=plan_id,
            session_id=session_id,
            title=title,
            description=description,
            template_id=template_id
        )

        # Create steps
        for i, step_data in enumerate(steps):
            step_id = str(uuid.uuid4())
            step = TaskStep(
                id=step_id,
                plan_id=plan_id,
                order=i + 1,
                title=step_data["title"],
                description=step_data["description"]
            )
            plan.steps.append(step)

        self.plans[plan_id] = plan
        db.save_task_plan(plan.to_dict())
        return plan

    def create_from_template(self, session_id: str, template_id: str) -> Optional[TaskPlan]:
        """
        Create a plan from a template

        Args:
            session_id: ID of the session
            template_id: ID of the template to use

        Returns:
            Created TaskPlan or None if template not found
        """
        template = self.templates.get(template_id)
        if not template:
            return None

        return self.create_plan(
            session_id=session_id,
            title=template.name,
            description=template.description,
            steps=template.steps,
            template_id=template_id
        )

    def create_from_message(self, session_id: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Auto-detect template from message and create a plan

        Returns dict with 'template' and 'plan' keys, or None if no match
        """
        template_match = self.detect_template(message)
        if not template_match:
            return None

        plan = self.create_from_template(session_id, template_match["id"])
        if not plan:
            return None

        return {
            "template": template_match,
            "plan": plan.to_dict()
        }

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific plan by ID"""
        plan = self.plans.get(plan_id)
        return plan.to_dict() if plan else None

    def get_plans_for_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all plans for a session"""
        plans = [p for p in self.plans.values() if p.session_id == session_id]
        plans.sort(key=lambda p: p.created_at, reverse=True)
        return [p.to_dict(include_steps=False) for p in plans]

    def get_active_plan(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the active (in-progress) plan for a session"""
        for plan in self.plans.values():
            if plan.session_id == session_id and plan.status == PlanStatus.IN_PROGRESS:
                return plan.to_dict()
        return None

    def start_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Start executing a plan

        Returns the plan with first step marked in_progress
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        if plan.status != PlanStatus.CREATED:
            return None  # Can only start a new plan

        plan.status = PlanStatus.IN_PROGRESS
        plan.started_at = datetime.now().isoformat()

        # Mark first step as in_progress
        if plan.steps:
            plan.steps[0].status = StepStatus.IN_PROGRESS
            plan.steps[0].started_at = datetime.now().isoformat()

        db.save_task_plan(plan.to_dict())
        return plan.to_dict()

    def complete_step(self, plan_id: str, step_id: str) -> Optional[Dict[str, Any]]:
        """
        Mark a step as completed and start the next one

        Returns dict with 'plan', 'completed_step', 'next_step' keys
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        # Find the step
        step = None
        step_index = -1
        for i, s in enumerate(plan.steps):
            if s.id == step_id:
                step = s
                step_index = i
                break

        if not step:
            return None

        # Mark step completed
        step.status = StepStatus.COMPLETED
        step.completed_at = datetime.now().isoformat()

        # Find next step
        next_step = None
        if step_index + 1 < len(plan.steps):
            next_step = plan.steps[step_index + 1]
            next_step.status = StepStatus.IN_PROGRESS
            next_step.started_at = datetime.now().isoformat()
        else:
            # All steps done
            plan.status = PlanStatus.COMPLETED
            plan.completed_at = datetime.now().isoformat()

        db.save_task_plan(plan.to_dict())
        return {
            "plan": plan.to_dict(),
            "completed_step": step.to_dict(),
            "next_step": next_step.to_dict() if next_step else None,
            "is_complete": plan.status == PlanStatus.COMPLETED
        }

    def fail_step(self, plan_id: str, step_id: str, error_message: str) -> Optional[Dict[str, Any]]:
        """
        Mark a step as failed

        Returns dict with 'plan' and 'failed_step' keys
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        # Find the step
        step = None
        for s in plan.steps:
            if s.id == step_id:
                step = s
                break

        if not step:
            return None

        step.status = StepStatus.FAILED
        step.error_message = error_message
        step.completed_at = datetime.now().isoformat()

        # Optionally mark plan as failed (or could continue with next step)
        plan.status = PlanStatus.FAILED

        db.save_task_plan(plan.to_dict())
        return {
            "plan": plan.to_dict(),
            "failed_step": step.to_dict()
        }

    def skip_step(self, plan_id: str, step_id: str) -> Optional[Dict[str, Any]]:
        """
        Skip a step and move to the next one

        Returns dict with 'plan', 'skipped_step', 'next_step' keys
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return None

        # Find the step
        step = None
        step_index = -1
        for i, s in enumerate(plan.steps):
            if s.id == step_id:
                step = s
                step_index = i
                break

        if not step:
            return None

        # Mark step skipped
        step.status = StepStatus.SKIPPED
        step.completed_at = datetime.now().isoformat()

        # Find next step
        next_step = None
        if step_index + 1 < len(plan.steps):
            next_step = plan.steps[step_index + 1]
            next_step.status = StepStatus.IN_PROGRESS
            next_step.started_at = datetime.now().isoformat()
        else:
            # All steps done (even if some skipped)
            plan.status = PlanStatus.COMPLETED
            plan.completed_at = datetime.now().isoformat()

        db.save_task_plan(plan.to_dict())
        return {
            "plan": plan.to_dict(),
            "skipped_step": step.to_dict(),
            "next_step": next_step.to_dict() if next_step else None,
            "is_complete": plan.status == PlanStatus.COMPLETED
        }

    def get_context_for_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get task context for a session (for Claude integration)

        Returns structured data about active tasks
        """
        active_plan = self.get_active_plan(session_id)

        if not active_plan:
            return {
                "has_active_plan": False,
                "plan": None,
                "current_step": None,
                "progress": None
            }

        return {
            "has_active_plan": True,
            "plan": {
                "id": active_plan["id"],
                "title": active_plan["title"],
                "description": active_plan["description"]
            },
            "current_step": active_plan.get("current_step"),
            "progress": active_plan.get("progress")
        }
