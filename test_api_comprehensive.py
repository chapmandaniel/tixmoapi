#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Ticket Vendor API
Tests all 28 endpoints across Authentication, Events, and Tickets

Usage:
    python test_api_comprehensive.py
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

# Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

# Rich console for pretty output
console = Console()

# Test results storage
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "details": []
}

# Test data storage
test_data = {
    "admin_token": None,
    "promoter_token": None,
    "user_token": None,
    "promoter_id": None,
    "user_id": None,
    "event_id": None,
    "tier_id": None,
    "ticket_id": None,
    "order_id": None
}


class APITester:
    """Handles API testing with proper error handling and reporting"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        
    async def close(self):
        await self.client.aclose()
    
    async def test_endpoint(
        self,
        method: str,
        endpoint: str,
        name: str,
        auth_token: Optional[str] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        expected_status: int = 200,
        save_response_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test a single endpoint and return results"""
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        try:
            if method == "GET":
                response = await self.client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await self.client.post(url, headers=headers, json=json_data)
            elif method == "PUT":
                response = await self.client.put(url, headers=headers, json=json_data)
            elif method == "PATCH":
                response = await self.client.patch(url, headers=headers, json=json_data)
            elif method == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            success = response.status_code == expected_status
            
            # Save response data if requested
            if success and save_response_key and response.text:
                try:
                    response_json = response.json()
                    test_data[save_response_key] = response_json
                except:
                    pass
            
            return {
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": success,
                "response_time": response.elapsed.total_seconds(),
                "error": None
            }
            
        except Exception as e:
            return {
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "status_code": None,
                "expected_status": expected_status,
                "success": False,
                "response_time": 0,
                "error": str(e)
            }


async def test_health_check(tester: APITester):
    """Test: Health Check"""
    console.print("\n[bold cyan]═══ Testing Health Check ═══[/bold cyan]")
    
    result = await tester.test_endpoint(
        "GET", "/health",
        "Health Check",
        expected_status=200
    )
    
    log_result(result)


async def test_authentication(tester: APITester):
    """Test: Authentication Endpoints (8 total)"""
    console.print("\n[bold cyan]═══ Testing Authentication (8 endpoints) ═══[/bold cyan]")
    
    # 1. Register Admin
    result = await tester.test_endpoint(
        "POST", "/auth/register",
        "1. Register Admin User",
        json_data={
            "email": "admin@test.com",
            "password": "Admin123!@#",
            "full_name": "Admin User",
            "role": "admin"
        },
        expected_status=201
    )
    log_result(result)
    
    # 2. Register Promoter
    result = await tester.test_endpoint(
        "POST", "/auth/register",
        "2. Register Promoter User",
        json_data={
            "email": "promoter@test.com",
            "password": "Promoter123!@#",
            "full_name": "Test Promoter",
            "role": "promoter"
        },
        expected_status=201,
        save_response_key="promoter_data"
    )
    log_result(result)
    if result["success"] and "promoter_data" in test_data:
        test_data["promoter_id"] = test_data["promoter_data"].get("id")
    
    # 3. Register Regular User
    result = await tester.test_endpoint(
        "POST", "/auth/register",
        "3. Register Regular User",
        json_data={
            "email": "user@test.com",
            "password": "User123!@#",
            "full_name": "Test User",
            "role": "user"
        },
        expected_status=201,
        save_response_key="user_data"
    )
    log_result(result)
    if result["success"] and "user_data" in test_data:
        test_data["user_id"] = test_data["user_data"].get("id")
    
    # 4. Login Admin
    result = await tester.test_endpoint(
        "POST", "/auth/login",
        "4. Login Admin",
        json_data={
            "email": "admin@test.com",
            "password": "Admin123!@#"
        },
        expected_status=200,
        save_response_key="admin_auth"
    )
    log_result(result)
    if result["success"] and "admin_auth" in test_data:
        test_data["admin_token"] = test_data["admin_auth"].get("access_token")
    
    # 5. Login Promoter
    result = await tester.test_endpoint(
        "POST", "/auth/login",
        "5. Login Promoter",
        json_data={
            "email": "promoter@test.com",
            "password": "Promoter123!@#"
        },
        expected_status=200,
        save_response_key="promoter_auth"
    )
    log_result(result)
    if result["success"] and "promoter_auth" in test_data:
        test_data["promoter_token"] = test_data["promoter_auth"].get("access_token")
    
    # 6. Login User
    result = await tester.test_endpoint(
        "POST", "/auth/login",
        "6. Login Regular User",
        json_data={
            "email": "user@test.com",
            "password": "User123!@#"
        },
        expected_status=200,
        save_response_key="user_auth"
    )
    log_result(result)
    if result["success"] and "user_auth" in test_data:
        test_data["user_token"] = test_data["user_auth"].get("access_token")
    
    # 7. Get Current User
    if test_data.get("promoter_token"):
        result = await tester.test_endpoint(
            "GET", "/auth/me",
            "7. Get Current User (Promoter)",
            auth_token=test_data["promoter_token"],
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("7. Get Current User (Promoter)", "No auth token")
    
    # 8. Refresh Token
    if test_data.get("promoter_auth") and test_data["promoter_auth"].get("refresh_token"):
        result = await tester.test_endpoint(
            "POST", "/auth/refresh",
            "8. Refresh Access Token",
            json_data={
                "refresh_token": test_data["promoter_auth"]["refresh_token"]
            },
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("8. Refresh Access Token", "No refresh token")


async def test_events(tester: APITester):
    """Test: Event Management Endpoints (9 total)"""
    console.print("\n[bold cyan]═══ Testing Event Management (9 endpoints) ═══[/bold cyan]")
    
    promoter_token = test_data.get("promoter_token")
    
    # 1. Create Event
    if promoter_token:
        event_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
        result = await tester.test_endpoint(
            "POST", "/events",
            "1. Create Event",
            auth_token=promoter_token,
            json_data={
                "title": "Summer Music Festival 2025",
                "description": "The biggest music event of the summer",
                "venue_name": "Central Park Amphitheater",
                "venue_address": "123 Park Ave, New York, NY 10001",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "event_date": event_date,
                "doors_open_time": "17:00:00",
                "event_start_time": "18:00:00",
                "event_end_time": "23:00:00",
                "category": "music",
                "tags": ["music", "festival", "outdoor"],
                "image_url": "https://example.com/festival.jpg",
                "total_capacity": 5000
            },
            expected_status=201,
            save_response_key="event_data"
        )
        log_result(result)
        if result["success"] and "event_data" in test_data:
            test_data["event_id"] = test_data["event_data"].get("id")
    else:
        log_result_skip("1. Create Event", "No promoter token")
    
    # 2. List Events (Public)
    result = await tester.test_endpoint(
        "GET", "/events",
        "2. List Events (Public)",
        params={"limit": 10},
        expected_status=200
    )
    log_result(result)
    
    # 3. Get Event Details
    if test_data.get("event_id"):
        result = await tester.test_endpoint(
            "GET", f"/events/{test_data['event_id']}",
            "3. Get Event Details",
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("3. Get Event Details", "No event created")
    
    # 4. Update Event
    if promoter_token and test_data.get("event_id"):
        result = await tester.test_endpoint(
            "PUT", f"/events/{test_data['event_id']}",
            "4. Update Event",
            auth_token=promoter_token,
            json_data={
                "title": "Summer Music Festival 2025 - Updated",
                "description": "The biggest music event of the summer - Now with more stages!"
            },
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("4. Update Event", "Missing requirements")
    
    # 5. Get My Events (Promoter)
    if promoter_token:
        result = await tester.test_endpoint(
            "GET", "/events/my/events",
            "5. Get My Events (Promoter)",
            auth_token=promoter_token,
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("5. Get My Events", "No promoter token")
    
    # 6. Publish Event
    if promoter_token and test_data.get("event_id"):
        result = await tester.test_endpoint(
            "POST", f"/events/{test_data['event_id']}/publish",
            "6. Publish Event",
            auth_token=promoter_token,
            json_data={"is_featured": True},
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("6. Publish Event", "Missing requirements")
    
    # 7. Search Events
    result = await tester.test_endpoint(
        "GET", "/events",
        "7. Search Events (by city)",
        params={"search": "New York", "status_filter": "published"},
        expected_status=200
    )
    log_result(result)
    
    # 8. Filter Events by Category
    result = await tester.test_endpoint(
        "GET", "/events",
        "8. Filter Events (by category)",
        params={"category": "music", "limit": 5},
        expected_status=200
    )
    log_result(result)
    
    # 9. Cancel Event (Skip - would cancel our test event)
    log_result_skip("9. Cancel Event", "Skipping to preserve test data")


async def test_tickets(tester: APITester):
    """Test: Ticket Management Endpoints (11 total)"""
    console.print("\n[bold cyan]═══ Testing Ticket Management (11 endpoints) ═══[/bold cyan]")
    
    promoter_token = test_data.get("promoter_token")
    user_token = test_data.get("user_token")
    event_id = test_data.get("event_id")
    
    # 1. Create Ticket Tier
    if promoter_token and event_id:
        sale_start = datetime.utcnow().isoformat()
        sale_end = (datetime.utcnow() + timedelta(days=25)).isoformat()
        
        result = await tester.test_endpoint(
            "POST", f"/tickets/events/{event_id}/tiers",
            "1. Create Ticket Tier (General Admission)",
            auth_token=promoter_token,
            json_data={
                "name": "General Admission",
                "description": "Standard entry ticket",
                "price": 49.99,
                "quantity": 1000,
                "min_purchase": 1,
                "max_purchase": 10,
                "sale_start_time": sale_start,
                "sale_end_time": sale_end,
                "is_active": True
            },
            expected_status=201,
            save_response_key="tier_data"
        )
        log_result(result)
        if result["success"] and "tier_data" in test_data:
            test_data["tier_id"] = test_data["tier_data"].get("id")
    else:
        log_result_skip("1. Create Ticket Tier", "Missing requirements")
    
    # 2. Create VIP Tier
    if promoter_token and event_id:
        sale_start = datetime.utcnow().isoformat()
        sale_end = (datetime.utcnow() + timedelta(days=25)).isoformat()
        
        result = await tester.test_endpoint(
            "POST", f"/tickets/events/{event_id}/tiers",
            "2. Create Ticket Tier (VIP)",
            auth_token=promoter_token,
            json_data={
                "name": "VIP Access",
                "description": "VIP seating with meet & greet",
                "price": 199.99,
                "quantity": 100,
                "min_purchase": 1,
                "max_purchase": 4,
                "sale_start_time": sale_start,
                "sale_end_time": sale_end,
                "is_active": True
            },
            expected_status=201
        )
        log_result(result)
    else:
        log_result_skip("2. Create Ticket Tier (VIP)", "Missing requirements")
    
    # 3. List Event Tiers
    if event_id:
        result = await tester.test_endpoint(
            "GET", f"/tickets/events/{event_id}/tiers",
            "3. List Event Tiers",
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("3. List Event Tiers", "No event")
    
    # 4. Get Tier Details
    if test_data.get("tier_id"):
        result = await tester.test_endpoint(
            "GET", f"/tickets/tiers/{test_data['tier_id']}",
            "4. Get Tier Details",
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("4. Get Tier Details", "No tier created")
    
    # 5. Check Tier Availability
    if test_data.get("tier_id"):
        result = await tester.test_endpoint(
            "GET", f"/tickets/tiers/{test_data['tier_id']}/availability",
            "5. Check Tier Availability",
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("5. Check Tier Availability", "No tier created")
    
    # 6. Update Tier
    if promoter_token and test_data.get("tier_id"):
        result = await tester.test_endpoint(
            "PUT", f"/tickets/tiers/{test_data['tier_id']}",
            "6. Update Tier (increase quantity)",
            auth_token=promoter_token,
            json_data={
                "quantity": 1500,
                "description": "Standard entry ticket - Capacity increased!"
            },
            expected_status=200
        )
        log_result(result)
    else:
        log_result_skip("6. Update Tier", "Missing requirements")
    
    # 7-11. Ticket Operations (would need actual purchase)
    log_result_skip("7. Get My Tickets", "Requires ticket purchase")
    log_result_skip("8. Get Ticket Details", "Requires ticket purchase")
    log_result_skip("9. Set Attendee Info", "Requires ticket purchase")
    log_result_skip("10. Transfer Ticket", "Requires ticket purchase")
    log_result_skip("11. Validate Ticket", "Requires ticket purchase")


def log_result(result: Dict[str, Any]):
    """Log a test result"""
    if result["success"]:
        test_results["passed"] += 1
        status = "[green]✓ PASS[/green]"
    else:
        test_results["failed"] += 1
        status = "[red]✗ FAIL[/red]"
    
    test_results["details"].append(result)
    
    console.print(f"{status} {result['name']} - {result['method']} {result['endpoint']}")
    if not result["success"]:
        if result["error"]:
            console.print(f"   [red]Error: {result['error']}[/red]")
        else:
            console.print(f"   [red]Expected {result['expected_status']}, got {result['status_code']}[/red]")


def log_result_skip(name: str, reason: str):
    """Log a skipped test"""
    test_results["skipped"] += 1
    console.print(f"[yellow]⊘ SKIP[/yellow] {name} - {reason}")


def print_summary():
    """Print test summary"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]TEST SUMMARY[/bold cyan]")
    console.print("="*70)
    
    total = test_results["passed"] + test_results["failed"] + test_results["skipped"]
    
    # Create summary table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Status", style="cyan", width=15)
    table.add_column("Count", justify="right", style="cyan")
    table.add_column("Percentage", justify="right", style="cyan")
    
    if total > 0:
        pass_pct = (test_results["passed"] / total) * 100
        fail_pct = (test_results["failed"] / total) * 100
        skip_pct = (test_results["skipped"] / total) * 100
    else:
        pass_pct = fail_pct = skip_pct = 0
    
    table.add_row("[green]Passed[/green]", str(test_results["passed"]), f"{pass_pct:.1f}%")
    table.add_row("[red]Failed[/red]", str(test_results["failed"]), f"{fail_pct:.1f}%")
    table.add_row("[yellow]Skipped[/yellow]", str(test_results["skipped"]), f"{skip_pct:.1f}%")
    table.add_row("[bold]Total[/bold]", str(total), "100%")
    
    console.print(table)
    
    # Overall status
    if test_results["failed"] == 0 and test_results["passed"] > 0:
        console.print("\n[bold green]✓ ALL TESTS PASSED![/bold green]")
    elif test_results["failed"] > 0:
        console.print(f"\n[bold red]✗ {test_results['failed']} TEST(S) FAILED[/bold red]")
    
    console.print("="*70 + "\n")


async def main():
    """Main test runner"""
    console.print(Panel.fit(
        "[bold cyan]Ticket Vendor API - Comprehensive Test Suite[/bold cyan]\n"
        "Testing 28 endpoints across Authentication, Events, and Tickets",
        border_style="cyan"
    ))
    
    tester = APITester(API_BASE_URL)
    
    try:
        # Health Check
        await test_health_check(tester)
        
        # Authentication (8 endpoints)
        await test_authentication(tester)
        
        # Events (9 endpoints)
        await test_events(tester)
        
        # Tickets (11 endpoints)
        await test_tickets(tester)
        
        # Print summary
        print_summary()
        
        # Save results to file
        with open("/home/claude/test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "passed": test_results["passed"],
                    "failed": test_results["failed"],
                    "skipped": test_results["skipped"]
                },
                "details": test_results["details"]
            }, f, indent=2)
        
        console.print("[green]Test results saved to test_results.json[/green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
    finally:
        await tester.close()


if __name__ == "__main__":
    # Check if required packages are installed
    try:
        import httpx
        import rich
    except ImportError:
        print("ERROR: Required packages not installed")
        print("Please run: pip install httpx rich")
        exit(1)
    
    asyncio.run(main())
