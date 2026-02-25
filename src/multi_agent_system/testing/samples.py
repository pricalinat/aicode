"""Test cases for e-commerce scenarios."""

from .test_assistant import (
    TestAnalysisAssistant,
    TestType,
    TestPriority,
    TestStatus,
    get_test_assistant,
)


def create_sample_tests() -> TestAnalysisAssistant:
    """Create sample test cases for demonstration."""
    assistant = get_test_assistant()

    # Test Case 1: Product Search
    tc1 = assistant.create_test_case(
        name="Product Search - Basic Search",
        description="Test basic product search functionality",
        test_type=TestType.INTEGRATION,
        priority=TestPriority.HIGH,
    )
    assistant.add_test_step(tc1.id, "Navigate to search page", "Search page loads")
    assistant.add_test_step(tc1.id, "Enter search query 'iPhone'", "Search results appear")
    assistant.add_test_step(tc1.id, "Verify results contain iPhone", "Results contain iPhone products")
    tc1.covers_module = "product_search"
    tc1.tags = ["search", "product"]

    # Test Case 2: Add to Cart
    tc2 = assistant.create_test_case(
        name="Add Product to Cart",
        description="Test adding product to shopping cart",
        test_type=TestType.E2E,
        priority=TestPriority.CRITICAL,
    )
    assistant.add_test_step(tc2.id, "Search for product", "Results displayed")
    assistant.add_test_step(tc2.id, "Click on product", "Product detail page opens")
    assistant.add_test_step(tc2.id, "Click 'Add to Cart'", "Product added successfully")
    assistant.add_test_step(tc2.id, "Verify cart shows product", "Cart contains product")
    tc2.covers_module = "cart"
    tc2.tags = ["cart", "purchase"]

    # Test Case 3: User Login
    tc3 = assistant.create_test_case(
        name="User Login - Valid Credentials",
        description="Test user login with valid credentials",
        test_type=TestType.UNIT,
        priority=TestPriority.CRITICAL,
    )
    assistant.add_test_step(tc3.id, "Navigate to login page", "Login page loads")
    assistant.add_test_step(tc3.id, "Enter valid email and password", "Credentials entered")
    assistant.add_test_step(tc3.id, "Click login button", "User logged in successfully")
    tc3.covers_module = "auth"
    tc3.tags = ["auth", "login"]

    # Test Case 4: Checkout Process
    tc4 = assistant.create_test_case(
        name="Checkout Process",
        description="Test complete checkout flow",
        test_type=TestType.E2E,
        priority=TestPriority.CRITICAL,
    )
    assistant.add_test_step(tc4.id, "Add product to cart", "Product in cart")
    assistant.add_test_step(tc4.id, "Proceed to checkout", "Checkout page loads")
    assistant.add_test_step(tc4.id, "Enter shipping address", "Address entered")
    assistant.add_test_step(tc4.id, "Select payment method", "Payment method selected")
    assistant.add_test_step(tc4.id, "Place order", "Order placed successfully")
    tc4.covers_module = "checkout"
    tc4.tags = ["checkout", "purchase"]

    # Test Case 5: Product Filter
    tc5 = assistant.create_test_case(
        name="Product Filter by Price",
        description="Test filtering products by price range",
        test_type=TestType.INTEGRATION,
        priority=TestPriority.MEDIUM,
    )
    assistant.add_test_step(tc5.id, "Navigate to product category", "Category page loads")
    assistant.add_test_step(tc5.id, "Set price range filter", "Filter applied")
    assistant.add_test_step(tc5.id, "Verify results match filter", "Results within price range")
    tc5.covers_module = "filter"
    tc5.tags = ["filter", "search"]

    # Test Case 6: User Registration
    tc6 = assistant.create_test_case(
        name="User Registration",
        description="Test new user registration",
        test_type=TestType.UNIT,
        priority=TestPriority.HIGH,
    )
    assistant.add_test_step(tc6.id, "Navigate to registration page", "Registration page loads")
    assistant.add_test_step(tc6.id, "Fill registration form", "Form filled")
    assistant.add_test_step(tc6.id, "Submit registration", "Account created")
    tc6.covers_module = "auth"
    tc6.tags = ["auth", "registration"]

    # Test Case 7: Payment Processing
    tc7 = assistant.create_test_case(
        name="Payment Processing - Credit Card",
        description="Test credit card payment processing",
        test_type=TestType.E2E,
        priority=TestPriority.CRITICAL,
    )
    assistant.add_test_step(tc7.id, "Proceed to payment", "Payment page loads")
    assistant.add_test_step(tc7.id, "Enter credit card details", "Card details entered")
    assistant.add_test_step(tc7.id, "Submit payment", "Payment processed successfully")
    tc7.covers_module = "payment"
    tc7.tags = ["payment", "checkout"]

    # Test Case 8: Product Review
    tc8 = assistant.create_test_case(
        name="Submit Product Review",
        description="Test submitting a product review",
        test_type=TestType.INTEGRATION,
        priority=TestPriority.LOW,
    )
    assistant.add_test_step(tc8.id, "Navigate to product", "Product page loads")
    assistant.add_test_step(tc8.id, "Click 'Write Review'", "Review form opens")
    assistant.add_test_step(tc8.id, "Submit review", "Review submitted successfully")
    tc8.covers_module = "review"
    tc8.tags = ["review", "product"]

    # Create test suite
    suite = assistant.create_test_suite(
        name="E-Commerce Core Tests",
        description="Main test suite for e-commerce functionality",
    )
    for tc in [tc1, tc2, tc3, tc4, tc5, tc6, tc7, tc8]:
        assistant.add_to_suite(suite.id, tc.id)

    return assistant
