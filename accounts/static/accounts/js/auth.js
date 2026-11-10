
// ===================================
// HOSTELMATE AUTHENTICATION SLIDER
// ===================================

const container = document.getElementById('container');

const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');

const mobileSignUp = document.getElementById('mobileSignUp');
const mobileSignIn = document.getElementById('mobileSignIn');


// Change authentication panel

function showSignUp() {
    container.classList.add('right-panel-active');
    sessionStorage.setItem('authPanel', 'signup');
}

function showSignIn() {
    container.classList.remove('right-panel-active');
    sessionStorage.setItem('authPanel', 'signin');
}


// Desktop buttons

signUpButton.addEventListener('click', showSignUp);
signInButton.addEventListener('click', showSignIn);


// Mobile buttons

mobileSignUp.addEventListener('click', showSignUp);
mobileSignIn.addEventListener('click', showSignIn);



// ===================================
// CATEGORY-SPECIFIC REGISTRATION FIELDS
// ===================================

const categorySelect = document.getElementById('category');
const categoryFields = document.getElementById('category-fields');


const categoryFormFields = {

    STUDENT: `
        <input type="text"
               name="institution_name"
               placeholder="Institution Name"
               required>

        <input type="text"
               name="course"
               placeholder="Course"
               required>

        <input type="text"
               name="study_year"
               placeholder="Year of Study"
               required>
    `,

    JOB_SEEKER: `
        <input type="text"
               name="qualification"
               placeholder="Highest Qualification"
               required>

        <input type="text"
               name="preferred_job_location"
               placeholder="Preferred Job Location"
               required>
    `,

    WORKING_PROFESSIONAL: `
        <input type="text"
               name="company_name"
               placeholder="Company Name"
               required>

        <input type="text"
               name="designation"
               placeholder="Designation"
               required>

        <input type="text"
               name="work_location"
               placeholder="Work Location"
               required>
    `,

    EXAM_ASPIRANT: `
        <input type="text"
               name="exam_name"
               placeholder="Exam Name"
               required>

        <input type="text"
               name="coaching_institute"
               placeholder="Coaching Institute">
    `,

    INTERN: `
        <input type="text"
               name="organisation"
               placeholder="Organisation Name"
               required>

        <input type="text"
               name="training_details"
               placeholder="Training / Course Details"
               required>
    `,

    BUSINESS: `
        <input type="text"
               name="business_name"
               placeholder="Business Name"
               required>

        <input type="text"
               name="business_type"
               placeholder="Business Type"
               required>
    `,

    MEDICAL: `
        <input type="text"
               name="hospital_name"
               placeholder="Hospital Name"
               required>

        <input type="text"
               name="visit_purpose"
               placeholder="Purpose of Visit"
               required>
    `,

    TEMPORARY: `
        <input type="text"
               name="stay_purpose"
               placeholder="Purpose of Stay"
               required>

        <input type="number"
               name="stay_duration"
               placeholder="Expected Duration (Days)"
               min="1"
               required>
    `,

    OTHER: `
        <input type="text"
               name="other_category"
               placeholder="Specify Your Category"
               required>

        <input type="text"
               name="other_purpose"
               placeholder="Purpose of Stay"
               required>
    `
};


// Display the appropriate fields

// ===================================
// RESTORE FORM DATA
// ===================================

const formDataElement = document.getElementById('form-data');

const formData = formDataElement
    ? JSON.parse(formDataElement.textContent)
    : {};



function showCategoryFields() {

    const selectedCategory = categorySelect.value;

    // Generate the appropriate input fields
    categoryFields.innerHTML =
        categoryFormFields[selectedCategory] || '';

    // Restore previously entered values
    categoryFields.querySelectorAll('input').forEach(input => {

        if (formData[input.name] !== undefined) {
            input.value = formData[input.name];
        }

    });
}


// Register the change listener BEFORE initial rendering
categorySelect.addEventListener('change', showCategoryFields);


// Restore the previously selected category
if (formData.category) {
    categorySelect.value = formData.category;
}


// Generate category fields immediately on page load
showCategoryFields();


// Restore normal signup fields
document.querySelectorAll('.sign-up-container input').forEach(input => {

    if (
        input.type !== 'password' &&
        formData[input.name] !== undefined
    ) {
        input.value = formData[input.name];
    }

});


// Restore the correct authentication panel
const initialPanel = container.dataset.initialPanel;

if (initialPanel === 'signin') {
    showSignIn();

} else if (initialPanel === 'signup') {
    showSignUp();

} else if (sessionStorage.getItem('authPanel') === 'signup') {
    container.classList.add('right-panel-active');

} else {
    showSignIn();
}
