# EdRoom Authentication UI

A modern React-based authentication interface for the EdRoom learning platform with sign-in and sign-up functionality.

## Features

✨ **Modern Authentication UI**
- Beautiful gradient backgrounds with animated elements
- Responsive design that works on all devices
- Smooth animations and transitions
- Form validation with real-time feedback

🔐 **Authentication System**
- User sign-in with email and password
- User registration with form validation
- Password visibility toggle
- Token-based authentication
- Persistent login sessions

🎨 **User Experience**
- Loading states and animations
- Error handling with user-friendly messages
- Demo credentials for testing
- Logout functionality
- Welcome messages with user names

## Demo Credentials

For testing the authentication system, use these demo credentials:

**Email:** `john@example.com`  
**Password:** `password123`

Other available demo users:
- `jane@example.com` / `mypassword`
- `admin@edroom.com` / `admin123`
- `student@test.com` / `student123`
- `teacher@edroom.com` / `teacher123`

## Getting Started

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Open in Browser**
   Navigate to `http://localhost:5173`

## Project Structure

```
src/
├── components/
│   └── AuthPage.jsx          # Main authentication component
├── utils/
│   └── auth.js              # Authentication utilities and API functions
├── App.jsx                  # Main app component with auth state management
├── ChatApp.jsx              # Main chat interface (post-authentication)
├── main.jsx                 # React entry point
└── index.css                # Global styles and animations
```

## Authentication Flow

1. **Initial Load**: App checks for existing authentication token
2. **Login/Register**: User submits credentials through AuthPage
3. **Validation**: Form validation and API authentication
4. **Success**: User is redirected to main ChatApp interface
5. **Session**: Authentication state is maintained until logout

## API Integration

The authentication system is designed to work with your backend API. Currently uses mock data for demonstration, but can be easily connected to real endpoints by updating the functions in `src/utils/auth.js`.

## Styling

- **Framework**: Tailwind CSS for utility-first styling
- **Icons**: Lucide React for consistent iconography
- **Animations**: Custom CSS animations for smooth transitions
- **Theme**: Modern gradient-based design with blue/purple color scheme

## Components

### AuthPage
- Handles both login and registration
- Form validation and error handling
- Animated UI elements
- Responsive design

### App
- Authentication state management
- Route protection
- Loading states
- User session handling

### ChatApp
- Main application interface
- User welcome messages
- Logout functionality
- Integration with existing chat features

## Customization

The authentication system is highly customizable:

- **Colors**: Update gradient colors in Tailwind classes
- **Animations**: Modify CSS animations in `index.css`
- **Validation**: Adjust validation rules in `AuthPage.jsx`
- **API**: Connect to real backend in `utils/auth.js`

## Security Features

- Client-side form validation
- Password strength requirements
- Token-based authentication
- Secure password input fields
- Session management

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is part of the EdRoom learning platform.
