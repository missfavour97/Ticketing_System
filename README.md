
# Ticketing System (Django)

A simple server-side web application for managing support tickets within an organization. Built using Django for a Server-Side Web Programming course.

---

##  Features

-  Hierarchical Unit Structure  
  Units can have parent-child relationships (e.g., IT Department → Network Team)

- Topics  
  Each unit can define support topics  

-  Ticket Management  
  Create tickets under a unit and topic  
  Track ticket status: New, In Progress, Done  
  Assign priority levels  

-  Comments System  
  Add comments to tickets and track progress  

- Dashboard  
  View system statistics (Units, Topics, Tickets)  

-  Status Updates  
  Update ticket status using buttons  

---

##  Technologies Used

- Python  
- Django  
- HTML  
- Bootstrap  
- SQLite  
- Conda  

---

##  Project Structure

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


##  Setup Instructions (Using Conda)

1. Create environment:
conda create -n ticketing_env python=3.11 -y

2. Activate environment:
conda activate ticketing_env

3. Install Django:
pip install django

4. Run migrations:
python manage.py migrate

5. Create superuser (optional):
python manage.py createsuperuser

6. Run server:
python manage.py runserver

---

##  Access the Application

Admin:
http://127.0.0.1:8000/admin/

Dashboard:
http://127.0.0.1:8000/api/ui/dashboard/

Units:
http://127.0.0.1:8000/api/ui/units/

Tickets:
http://127.0.0.1:8000/api/ui/tickets/

---

##  Usage

1. Create Units (with optional parent units)
2. Create Topics under Units
3. Create Tickets
4. Add Comments
5. Update Ticket Status
6. View Dashboard statistics

---

##  Notes

- This project is simple and functional as required
- Authentication is not implemented
- Focus is on backend logic and server-side rendering

---

##  Author

Favour Okwudili
Samira Alhousseini Maiga
Computer Engineering Students
