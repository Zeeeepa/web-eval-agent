# Web Eval Test Application - Comprehensive Testing Instructions

## Homepage Navigation Test

**Description:**
Test the basic navigation and homepage functionality of the web application.

**Steps:**
1. Navigate to the homepage at http://localhost:5000
2. Verify the page loads completely with the welcome message
3. Check that all navigation links are visible and clickable
4. Click on each feature card to verify navigation works
5. Verify the counter value is displayed in the jumbotron

**Validations:**
- Page loads within 5 seconds
- No console errors are present
- All navigation links are functional
- Feature cards are interactive and clickable
- Counter value is displayed correctly

**Expected Outcomes:**
- Homepage displays the welcome message and feature overview
- All navigation elements work properly
- Feature cards have hover effects and are clickable
- No JavaScript errors occur during page load

**Priority:** high
**Tags:** #navigation #homepage #basic

## Interactive Counter Test

**Description:**
Test the counter functionality with increment, decrement, and reset operations.

**Steps:**
1. Navigate to the Counter page (/counter)
2. Click the "Increment" button 3 times
3. Verify the counter shows 3
4. Click the "Decrement" button 1 time
5. Verify the counter shows 2
6. Click the "Reset" button
7. Verify the counter shows 0
8. Click "Decrement" 2 times to test negative numbers
9. Verify status badges update correctly (Positive/Negative/Zero)

**Validations:**
- Counter value updates correctly with each button click
- Status badges reflect the current counter state
- Even/Odd badge updates appropriately
- No console errors occur during interactions
- Button animations work properly

**Expected Outcomes:**
- All counter operations work as expected
- Status indicators update in real-time
- Button interactions are smooth and responsive
- Counter can handle positive, negative, and zero values

**Priority:** high
**Tags:** #counter #buttons #state-management

## Contact Form Validation Test

**Description:**
Test the contact form with both valid and invalid submissions to verify validation.

**Steps:**
1. Navigate to the Forms page (/forms)
2. Try submitting the form with all fields empty
3. Verify validation errors appear
4. Fill in valid data:
   - Name: "John Doe"
   - Email: "john.doe@example.com"
   - Subject: "General Inquiry"
   - Message: "This is a test message for web-eval validation"
5. Check the terms and conditions checkbox
6. Submit the form
7. Verify success page appears
8. Test invalid email format submission
9. Test form with missing required fields

**Validations:**
- Form validation prevents submission with empty required fields
- Email validation works for invalid formats
- Terms checkbox is required for submission
- Success message appears after valid submission
- Error messages are clear and helpful

**Expected Outcomes:**
- Form validation works correctly for all fields
- Valid submissions redirect to success page
- Invalid submissions show appropriate error messages
- No console errors occur during form interactions

**Priority:** high
**Tags:** #forms #validation #contact

## Todo List AJAX Operations Test

**Description:**
Test the todo list application with AJAX operations for adding, completing, and deleting todos.

**Steps:**
1. Navigate to the Todo page (/todo)
2. Add a new todo item: "Test todo item 1"
3. Verify the todo appears in the list
4. Add another todo: "Test todo item 2"
5. Mark the first todo as completed by checking the checkbox
6. Verify the todo appears crossed out
7. Uncheck the completed todo
8. Delete one of the todos using the delete button
9. Verify the todo statistics update correctly

**Validations:**
- New todos are added without page reload
- Todo completion status updates in real-time
- Delete functionality works properly
- Statistics (Total, Completed, Remaining) update correctly
- No console errors occur during AJAX operations

**Expected Outcomes:**
- All todo operations work smoothly with AJAX
- Real-time updates without page refreshes
- Statistics reflect current todo state
- User interface remains responsive during operations

**Priority:** high
**Tags:** #todo #ajax #crud-operations

## Newsletter Signup Test

**Description:**
Test the newsletter signup form with validation and success feedback.

**Steps:**
1. Navigate to the Forms page (/forms)
2. Scroll down to the Newsletter Signup section
3. Try submitting with an empty email field
4. Verify error message appears
5. Enter an invalid email format (e.g., "invalid-email")
6. Verify validation error
7. Enter a valid email: "test@example.com"
8. Submit the form
9. Verify success message appears

**Validations:**
- Email field validation works correctly
- Empty submissions are prevented
- Invalid email formats are rejected
- Success message appears for valid submissions
- Form resets after successful submission

**Expected Outcomes:**
- Newsletter signup form validates email properly
- Success feedback is provided to users
- Form behavior is consistent and user-friendly
- No console errors during form interactions

**Priority:** medium
**Tags:** #newsletter #forms #validation

## Modal Dialog Test

**Description:**
Test modal dialog functionality including opening, closing, and interaction.

**Steps:**
1. Navigate to the Forms page (/forms)
2. Click on the "Terms and Conditions" link in the contact form
3. Verify the modal opens properly
4. Read the terms content
5. Click "Accept" button
6. Verify the modal closes and terms checkbox is checked
7. Open the modal again
8. Click "Close" button to test alternative closing method
9. Click outside the modal to test backdrop closing

**Validations:**
- Modal opens when terms link is clicked
- Modal content is displayed correctly
- Accept button checks the terms checkbox
- Modal can be closed using multiple methods
- No console errors occur during modal interactions

**Expected Outcomes:**
- Modal dialogs work smoothly
- User interactions are intuitive
- Terms acceptance updates the form properly
- Modal behavior is consistent across different closing methods

**Priority:** medium
**Tags:** #modal #dialog #ui-interaction
