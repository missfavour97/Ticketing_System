
# University Support Ticketing System (Django)

A realistic, demonstrable server-side web application for managing university support tickets. Built with Django for a Server-Side Web Programming course.

---

## Features

- Login with role-based demo accounts for Admin, Unit Staff, and Student users

- Hierarchical support units and service topics

- Ticket queue with search and filters by status, priority, unit, and assignee

- Ticket detail page with comments, status history, requester, assignee, and SLA target

- Realistic ticket workflow: New, In Progress, Done, Canceled, Withdrawn

- Priority levels, staff assignment, unassigned queue, and SLA breach indicators

- Dashboard statistics for open tickets, high priority tickets, SLA risks, units, topics, and recent activity

- Optional Google reCAPTCHA on the login page

---

## Technologies Used

- Python  
- Django  
- HTML  
- Bootstrap  
- SQLite  
- Conda  

---

## Project Structure

Ticketing_System/
│
├── tickets/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/tickets/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│
└── manage.py


## Setup Instructions (Using Conda)

1. Create environment:
conda create -n ticketing_env python=3.11 -y

2. Activate environment:
conda activate ticketing_env

3. Install Django:
pip install django

4. Run migrations:
python manage.py migrate

5. Load realistic demo data:
python manage.py seed_demo

6. Run server:
python manage.py runserver

---

## reCAPTCHA Setup

The login form always shows a human verification step.
For class demos, it uses a local demo reCAPTCHA checkbox by default.

For real Google reCAPTCHA, create a checkbox key in Google Cloud and set both keys before starting Django:

```bash
export RECAPTCHA_SITE_KEY="your-site-key"
export RECAPTCHA_SECRET_KEY="your-secret-key"
python manage.py runserver
```

To turn off the classroom demo checkbox:

```bash
export RECAPTCHA_DEMO_MODE=0
python manage.py runserver
```

Do not commit the secret key to the repository.

---

## Demo Accounts

After running `python manage.py seed_demo`, you can log in with:

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin_demo` | `demo12345` |
| Unit Staff | `staff_it` | `demo12345` |
| Student | `student_ada` | `demo12345` |

---

## Access the Application

Admin:
http://127.0.0.1:8000/admin/

Dashboard:
http://127.0.0.1:8000/api/ui/dashboard/

Units:
http://127.0.0.1:8000/api/ui/units/

Tickets:
http://127.0.0.1:8000/api/ui/tickets/

---

## Demo Flow

1. Log in as `student_ada` and create a new support ticket.
2. Log out, then log in as `staff_it`.
3. Open the ticket queue and filter by unassigned or high-priority tickets.
4. Open a ticket detail page, assign it to staff, add a comment, and move it to In Progress.
5. Log in as `admin_demo` to show the full dashboard, units, topics, and all tickets.

---

## Notes

- This project is designed for education and classroom demonstration.
- The default SQLite database is fine for local demos.
- reCAPTCHA is optional and only appears when keys are configured.
- For a production system, move all secrets to environment variables, enforce stronger permissions, and review deployment security settings.

---

## Author

Favour Okwudili
Samira Alhousseini Maiga
Computer Engineering Students
