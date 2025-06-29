# Advanced E-commerce Platform with Django & DRF

A comprehensive e-commerce platform built with a robust Django REST Framework API backend and a user-friendly,
server-side rendered front end using Django templates and Bootstrap.

---

## Overview

This project is a complete e-commerce solution designed to showcase a full-stack development workflow. It features a
secure and powerful backend API for managing products, categories, users, carts, and orders, complete with JWT
authentication and a mock payment integration.

The project also includes a polished, server-side rendered website that allows users to browse products, register for an
account, manage their shopping cart, and complete a checkout process using a built-in mock credits system.

## Features

### Backend API (Powered by Django REST Framework)

- **Product & Category Management:** Full CRUD operations for products and hierarchical categories.
- **Custom User Model:** Extends Django's user to include address details and e-commerce credits.
- **JWT Authentication:** Secure API access using JSON Web Tokens (`djangorestframework-simplejwt`).
- **Granular Permissions:** Role-based access control (e.g., only admins can create products).
- **Server-Side Shopping Cart:** Persistent cart for each authenticated user with endpoints to add, update, and remove
  items.
- **Stock Validation:** Prevents adding more items to a cart than are available in stock.
- **Order Processing:** Endpoints to create orders from the cart, decrement stock, and view order history.
- **Mock Payment Integration:** Server-side logic to create payment intents and confirm orders.
- **Automated Testing:** A comprehensive test suite using `APITestCase` and `factory-boy` to ensure API reliability.

### Web Interface (Powered by Django & Bootstrap)

- **Professional Design:** Clean, responsive, and modern UI built with Bootstrap 5.
- **Server-Side Rendering:** A fast and traditional web experience powered entirely by Django's templating engine.
- **User Authentication Flow:** Custom-styled pages for user registration, login, and logout.
- **Interactive Shopping Cart:** View cart contents, update item quantities, and remove items.
- **Multi-Step Checkout:** A complete checkout process where users can confirm their address and use mock credits for
  payment.
- **Order Management:** A dedicated "My Orders" page for users to view their order history and status.
- **Dynamic User Feedback:** Uses Django's messages framework for clear success and error notifications.

## Technologies Used

* **Backend:** Python, Django, Django REST Framework, PostgreSQL
* **API & Authentication:** `djangorestframework-simplejwt`
* **Database Adapter:** `psycopg2-binary`
* **Image Handling:** `Pillow`
* **Testing:** `factory-boy`, `Faker`
* **Frontend:** Django Templates, Bootstrap 5 (via CDN)
* **Development:** Git, Virtual Environment (`venv`)

## Setup and Installation

Follow these steps to get the project running on your local machine.

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Levelcoder123/django-ecommerce-project.git
   cd e_commerce_store
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   This project uses a `requirements.txt` file to manage its packages.
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL Database:**
    * Ensure PostgreSQL is installed and running.
    * Create a new database and a user for the project.
        ```sql
        -- Example commands in psql
        CREATE DATABASE ecommerce_db;
        CREATE USER ecommerce_user WITH PASSWORD 'yourpassword';
        GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO ecommerce_user;
        ALTER ROLE ecommerce_user CREATEDB; -- Needed to run the test suite
        ```

5. **Configure Django Settings:**
    * In `ecommerce_project/settings.py`, update the `DATABASES` setting with your PostgreSQL credentials.
    * Set your own unique `SECRET_KEY`.

6. **Run Database Migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Create a Superuser (Admin Account):**
   ```bash
   python manage.py createsuperuser
   ```

## How to Run

1. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   The application will be accessible at `http://127.0.0.1:8000/`.

2. **Run Tests:**
   To verify all functionality, run the test suite:
   ```bash
   python manage.py test
   ```
