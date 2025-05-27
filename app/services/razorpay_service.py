import requests
import base64
import json
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RazorpayClient:
    """Razorpay API Client for eMandate operations"""
    
    def __init__(self):
        self.api_key = settings.razorpay_key_id
        self.api_secret = settings.razorpay_key_secret
        self.base_url = settings.razorpay_base_url
        self.auth_token = base64.b64encode(
            f"{self.api_key}:{self.api_secret}".encode()
        ).decode()
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {self.auth_token}'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[Any, Any]:
        """Make HTTP request to Razorpay API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.info("Making Razorpay API request", 
                       method=method, url=url, data=data)
            
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            response_data = response.json() if response.content else {}
            
            logger.info("Razorpay API response", 
                       status_code=response.status_code, 
                       response=response_data)
            
            if response.status_code >= 400:
                raise Exception(f"Razorpay API Error: {response_data}")
            
            return response_data
            
        except Exception as e:
            logger.error("Razorpay API request failed", error=str(e))
            raise
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a customer in Razorpay"""
        return self._make_request("POST", "customers", customer_data)
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer details from Razorpay"""
        return self._make_request("GET", f"customers/{customer_id}")
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an order in Razorpay"""
        return self._make_request("POST", "orders", order_data)
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details from Razorpay"""
        return self._make_request("GET", f"orders/{order_id}")
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Get payment details from Razorpay"""
        return self._make_request("GET", f"payments/{payment_id}")
    
    def capture_payment(self, payment_id: str, amount: int) -> Dict[str, Any]:
        """Capture a payment"""
        data = {"amount": amount}
        return self._make_request("POST", f"payments/{payment_id}/capture", data)
    
    def refund_payment(self, payment_id: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """Refund a payment"""
        data = {}
        if amount:
            data["amount"] = amount
        return self._make_request("POST", f"payments/{payment_id}/refund", data)


class MockRazorpayClient:
    """Mock Razorpay client for testing and development"""
    
    def __init__(self):
        self.mock_data = {
            "customers": {},
            "orders": {},
            "payments": {},
            "mandates": {}
        }
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock create customer"""
        customer_id = f"cust_mock_{len(self.mock_data['customers']) + 1}"
        customer = {
            "id": customer_id,
            "entity": "customer",
            "name": customer_data.get("name"),
            "email": customer_data.get("email"),
            "contact": customer_data.get("contact"),
            "gstin": customer_data.get("gstin"),
            "notes": customer_data.get("notes", {}),
            "created_at": 1234567890
        }
        self.mock_data["customers"][customer_id] = customer
        return customer
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Mock get customer"""
        return self.mock_data["customers"].get(customer_id, {})
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock create order"""
        order_id = f"order_mock_{len(self.mock_data['orders']) + 1}"
        order = {
            "id": order_id,
            "entity": "order",
            "amount": order_data.get("amount"),
            "amount_paid": 0,
            "amount_due": order_data.get("amount"),
            "currency": order_data.get("currency", "INR"),
            "receipt": order_data.get("receipt"),
            "status": "created",
            "attempts": 0,
            "notes": order_data.get("notes", {}),
            "created_at": 1234567890
        }
        self.mock_data["orders"][order_id] = order
        return order
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Mock get order"""
        return self.mock_data["orders"].get(order_id, {})
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Mock get payment"""
        return self.mock_data["payments"].get(payment_id, {})
    
    def capture_payment(self, payment_id: str, amount: int) -> Dict[str, Any]:
        """Mock capture payment"""
        payment = self.mock_data["payments"].get(payment_id, {})
        if payment:
            payment["status"] = "captured"
            payment["amount"] = amount
        return payment
    
    def refund_payment(self, payment_id: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """Mock refund payment"""
        refund_id = f"rfnd_mock_{len(self.mock_data['payments']) + 1}"
        return {
            "id": refund_id,
            "entity": "refund",
            "amount": amount,
            "currency": "INR",
            "payment_id": payment_id,
            "status": "processed",
            "created_at": 1234567890
        }


# Factory function to get the appropriate client
def get_razorpay_client():
    """Get Razorpay client based on environment"""
    if settings.environment == "development" or settings.debug:
        return MockRazorpayClient()
    return RazorpayClient()
