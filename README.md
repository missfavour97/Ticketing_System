
# University Support Ticketing System (Django)

A realistic, demonstrable server-side web application for managing university support tickets. Built with Django for a Server-Side Web Programming course.

---

## Features

- Login with role-based demo accounts for Admin, Unit Staff, and Student users

- Hierarchical support units and service topics

- Triage Desk department for reviewing unclear requests and routing tickets to the correct unit

- Ticket queue with search and filters by status, priority, unit, and assignee

- Tickets Board for staff/admin that groups tickets by New, In Progress, Done, Canceled, and Withdrawn

- Ticket detail page with comments, status history, requester, assignee, and SLA target

- File attachments on ticket creation and ticket detail pages

- Email notifications when tickets are created and when ticket status changes

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

## File Uploads

Uploaded files are stored locally in the `media/attachments/` folder during development.
Django serves these files through `/media/` while `DEBUG=True`.

---

## Email Notifications

By default, email notifications are printed in the terminal where `python manage.py runserver` is running.
This makes the feature easy to demonstrate without Gmail, SMTP, or paid email services.

To send real emails, configure Django's SMTP settings:

```bash
export EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
export EMAIL_HOST="smtp.example.com"
export EMAIL_PORT="587"
export EMAIL_HOST_USER="your-email@example.com"
export EMAIL_HOST_PASSWORD="your-email-password"
export DEFAULT_FROM_EMAIL="University Support <your-email@example.com>"
python manage.py runserver
```

Ticket creation emails and status change emails are sent to the ticket's notification email.

---

## Demo Accounts

After running `python manage.py seed_demo`, you can log in with:

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin_demo` | `demo12345` |
| Triage Staff | `staff_triage` | `demo12345` |
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

Tickets Board:
http://127.0.0.1:8000/api/ui/tickets/board/

---

## Demo Flow

1. Log in as `student_ada` and create a new support ticket.
2. Add a notification email and upload a supporting file.
3. Check the terminal to show the ticket-created email.
4. Log out, then log in as `staff_triage`.
5. Open the sample Triage Desk ticket and route it to the correct support unit/topic.
6. Log out, then log in as `staff_it`.
7. Open the ticket queue and filter by unassigned or high-priority tickets.
8. Open the Tickets Board to show tickets grouped by workflow status.
9. Open a ticket detail page, assign it to staff, add a comment, and move it to In Progress.
10. Check the terminal again to show the status-change email.
11. Log in as `admin_demo` to show the full dashboard, units, topics, and all tickets.

---

## Notes

- This project is designed for education and classroom demonstration.
- The default SQLite database is fine for local demos.
- The login page uses a demo reCAPTCHA checkbox unless real Google keys are configured.
- For a production system, move all secrets to environment variables, enforce stronger permissions, and review deployment security settings.

---

## Author

Favour Okwudili
Samira Alhousseini Maiga
Computer Engineering Students
