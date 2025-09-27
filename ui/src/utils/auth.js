// Authentication utilities for EdRoom

// ------------------- Types -------------------
export const createUser = (email, firstName, lastName, id) => ({
  email,
  firstName,
  lastName,
  id
});

export const createAuthResponse = (success, user = null, token = null, message = '', errors = null) => ({
  success,
  user,
  token,
  message,
  errors
});

// ------------------- Mock Data -------------------
const getUsersData = () => {
  // Simulate reading from users database
  return `john@example.com,password123,John,Doe
jane@example.com,mypassword,Jane,Smith
admin@edroom.com,admin123,Admin,User
student@test.com,student123,Test,Student
teacher@edroom.com,teacher123,Sarah,Johnson`;
};

// ------------------- Helpers -------------------
const parseUsersData = () => {
  const data = getUsersData();
  return data
    .split("\n")
    .filter(line => line.trim().length > 0)
    .map(line => {
      const [email, password, firstName, lastName] = line.split(",");
      return { email, password, firstName, lastName };
    });
};

// Generate a random token
const generateToken = () => {
  return `token_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`;
};

// Generate a random user ID
const generateUserId = () => {
  return Math.random().toString(36).substr(2, 9);
};

// ------------------- Auth Functions -------------------

// Authenticate user (login)
export const authenticateUser = async (email, password) => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));

  try {
    const users = parseUsersData();
    const user = users.find(u => u.email === email && u.password === password);

    if (user) {
      const authUser = createUser(
        user.email,
        user.firstName,
        user.lastName,
        generateUserId()
      );

      return createAuthResponse(
        true,
        authUser,
        generateToken(),
        "Login successful"
      );
    }

    return createAuthResponse(
      false,
      null,
      null,
      "Invalid email or password",
      { general: "Invalid email or password" }
    );
  } catch (error) {
    console.error('Authentication error:', error);
    return createAuthResponse(
      false,
      null,
      null,
      "Authentication failed",
      { general: "Network error occurred" }
    );
  }
};

// Register user
export const registerUser = async (email, password, firstName, lastName) => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1200));

  try {
    const users = parseUsersData();
    const existingUser = users.find(u => u.email === email);

    if (existingUser) {
      return createAuthResponse(
        false,
        null,
        null,
        "User already exists",
        { email: "This email is already registered" }
      );
    }

    // Simulated registration (not persisted in this demo)
    const newUser = createUser(email, firstName, lastName, generateUserId());

    return createAuthResponse(
      true,
      newUser,
      generateToken(),
      "Registration successful"
    );
  } catch (error) {
    console.error('Registration error:', error);
    return createAuthResponse(
      false,
      null,
      null,
      "Registration failed",
      { general: "Network error occurred" }
    );
  }
};

// Validate token
export const validateToken = (token) => {
  return !!token && token.startsWith("token_");
};

// Get current user from token
export const getCurrentUser = () => {
  const token = localStorage.getItem('authToken');
  if (!validateToken(token)) {
    return null;
  }
  
  // In a real app, you would decode the token or make an API call
  // For demo purposes, return a mock user
  return createUser(
    'user@example.com',
    'Current',
    'User',
    'current_user_id'
  );
};

// Logout user
export const logoutUser = () => {
  localStorage.removeItem('authToken');
  return true;
};

// Check if user is authenticated
export const isAuthenticated = () => {
  const token = localStorage.getItem('authToken');
  return validateToken(token);
};
