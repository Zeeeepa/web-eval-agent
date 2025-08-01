# Form Testing Instructions

## Contact Form Test

**Description:**
Test the contact form functionality including validation, submission, and error handling.

**Steps:**
1. Navigate to the contact form page
2. Fill out all required fields with valid data:
   - Name: "John Doe"
   - Email: "john.doe@example.com"
   - Subject: "Test Message"
   - Message: "This is a test message to verify form functionality."
3. Submit the form
4. Verify success message or confirmation
5. Test form validation by submitting with invalid data:
   - Empty required fields
   - Invalid email format
   - Extremely long input values

**Validations:**
- Form accepts valid input data
- Required field validation works correctly
- Email format validation is functional
- Success message appears after valid submission
- Error messages are clear and helpful
- Form doesn't submit with invalid data

**Expected Outcomes:**
- Valid form submission succeeds
- Invalid submissions show appropriate error messages
- Form validation prevents submission of bad data
- User receives clear feedback on form status
- No JavaScript errors occur during form interaction

**Priority:** high
**Tags:** #forms #validation #contact

## Newsletter Signup Test

**Description:**
Test the newsletter signup form functionality.

**Steps:**
1. Locate the newsletter signup form
2. Enter a valid email address: "test@example.com"
3. Submit the form
4. Verify confirmation message
5. Test with invalid email format
6. Test with empty email field

**Validations:**
- Valid email addresses are accepted
- Invalid email formats are rejected
- Empty submissions are prevented
- Confirmation message appears for valid submissions
- Error messages are displayed for invalid inputs

**Expected Outcomes:**
- Newsletter signup works with valid emails
- Form validation prevents invalid submissions
- User receives appropriate feedback
- No console errors occur

**Priority:** medium
**Tags:** #forms #newsletter #validation
