"""Interactive context gathering for user-provided innovation details."""
from typing import Dict, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()


@dataclass
class UserContext:
    """User-provided context about their innovation."""
    novel_aspect: str  # What's unique about the approach
    technology_details: str  # Technical details and methodology
    problem_solved: str  # Problem being addressed
    use_cases: Optional[str] = None  # Specific examples
    confidential_info: Optional[str] = None  # What NOT to mention
    additional_notes: Optional[str] = None  # Any other relevant info
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        result = {
            'novel_aspect': self.novel_aspect,
            'technology_details': self.technology_details,
            'problem_solved': self.problem_solved,
        }
        if self.use_cases:
            result['use_cases'] = self.use_cases
        if self.confidential_info:
            result['confidential_info'] = self.confidential_info
        if self.additional_notes:
            result['additional_notes'] = self.additional_notes
        return result


def gather_user_context(interactive: bool = True) -> Optional[UserContext]:
    """Interactively gather user context about their innovation.
    
    Args:
        interactive: Whether to prompt user interactively
        
    Returns:
        UserContext object if provided, None otherwise
    """
    if not interactive:
        return None
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Additional Context Gathering[/bold cyan]\n\n"
        "Help us write a better article by providing details about your innovation.\n"
        "This information will guide our research and ensure your novel approach\n"
        "is prominently featured in the article.",
        border_style="cyan"
    ))
    
    if not Confirm.ask("\n[bold]Would you like to provide additional context about your innovation?[/bold]", default=True):
        return None
    
    console.print("\n[dim]You can press Enter to skip optional questions.[/dim]\n")
    
    # Gather required information
    novel_aspect = Prompt.ask(
        "[bold]1. What is novel/unique about your approach?[/bold]\n"
        "   (2-3 sentences describing what makes your approach different)",
        default=""
    ).strip()
    
    if not novel_aspect:
        console.print("[yellow]Skipping context gathering - no novel aspect provided.[/yellow]")
        return None
    
    technology_details = Prompt.ask(
        "\n[bold]2. What specific technology/methodology are you using?[/bold]\n"
        "   (1-2 paragraphs describing your technical approach)",
        default=""
    ).strip()
    
    if not technology_details:
        console.print("[yellow]Warning: No technology details provided.[/yellow]")
    
    problem_solved = Prompt.ask(
        "\n[bold]3. What problem does this solve?[/bold]\n"
        "   (1-2 sentences describing the problem you're addressing)",
        default=""
    ).strip()
    
    if not problem_solved:
        console.print("[yellow]Warning: No problem description provided.[/yellow]")
    
    # Optional information
    use_cases = Prompt.ask(
        "\n[bold]4. Any specific examples or use cases?[/bold] (optional)\n"
        "   (Press Enter to skip)",
        default=""
    ).strip() or None
    
    confidential_info = Prompt.ask(
        "\n[bold]5. Any confidential names/details to avoid mentioning?[/bold] (optional)\n"
        "   (e.g., 'ProductName - do not mention this name')",
        default=""
    ).strip() or None
    
    additional_notes = Prompt.ask(
        "\n[bold]6. Any additional notes or details?[/bold] (optional)\n"
        "   (Press Enter to skip)",
        default=""
    ).strip() or None
    
    # Create context object
    context = UserContext(
        novel_aspect=novel_aspect,
        technology_details=technology_details or "Not specified",
        problem_solved=problem_solved or "Not specified",
        use_cases=use_cases,
        confidential_info=confidential_info,
        additional_notes=additional_notes
    )
    
    # Display summary for confirmation
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Context Summary[/bold green]\n\n"
        f"[bold]Novel Aspect:[/bold]\n{novel_aspect}\n\n"
        f"[bold]Technology Details:[/bold]\n{technology_details or 'Not provided'}\n\n"
        f"[bold]Problem Solved:[/bold]\n{problem_solved or 'Not provided'}\n"
        + (f"\n[bold]Use Cases:[/bold]\n{use_cases}\n" if use_cases else "")
        + (f"\n[bold]Confidential Info:[/bold]\n{confidential_info}\n" if confidential_info else ""),
        border_style="green"
    ))
    
    if Confirm.ask("\n[bold]Use this context for article generation?[/bold]", default=True):
        return context
    else:
        console.print("[yellow]Context gathering cancelled.[/yellow]")
        return None


def load_context_from_file(file_path: str) -> Optional[UserContext]:
    """Load user context from a JSON file.
    
    Args:
        file_path: Path to JSON file with context data
        
    Returns:
        UserContext object if loaded successfully, None otherwise
    """
    import json
    from pathlib import Path
    
    try:
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]Context file not found: {file_path}[/red]")
            return None
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return UserContext(
            novel_aspect=data.get('novel_aspect', ''),
            technology_details=data.get('technology_details', ''),
            problem_solved=data.get('problem_solved', ''),
            use_cases=data.get('use_cases'),
            confidential_info=data.get('confidential_info'),
            additional_notes=data.get('additional_notes')
        )
    except Exception as e:
        console.print(f"[red]Error loading context file: {e}[/red]")
        return None
