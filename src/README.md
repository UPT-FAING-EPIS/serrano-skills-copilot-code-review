# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up or unregister students from activities (teacher login required)
- Display active announcements from the database
- Manage announcements (create, edit, delete) for signed-in users

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

### Activities

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/activities` | Get all activities and their details (supports `day`, `start_time`, `end_time` filters) |
| GET | `/activities/days` | Get all days that have scheduled activities |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu&teacher_username=<username>` | Register a student in an activity (requires signed-in teacher) |
| POST | `/activities/{activity_name}/unregister?email=student@mergington.edu&teacher_username=<username>` | Remove a student from an activity (requires signed-in teacher) |

### Authentication

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/auth/login?username=<username>&password=<password>` | Sign in and return teacher profile |
| GET | `/auth/check-session?username=<username>` | Validate a teacher session by username |

### Announcements

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET | `/announcements/active` | Get announcements currently active for public display |
| GET | `/announcements?teacher_username=<username>` | Get all announcements for management (requires signed-in teacher) |
| POST | `/announcements?teacher_username=<username>` | Create announcement (`message`, `expires_at`, optional `starts_at`) |
| PUT | `/announcements/{announcement_id}?teacher_username=<username>` | Update announcement (`message`, `expires_at`, optional `starts_at`) |
| DELETE | `/announcements/{announcement_id}?teacher_username=<username>` | Delete an announcement |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Data is stored in MongoDB. The app seeds example activities, teacher accounts, and an example announcement when collections are empty.
