
// ===================================
// HOSTELMATE AUTHENTICATION SLIDER
// ===================================

const container = document.getElementById('container');

const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');

const mobileSignUp = document.getElementById('mobileSignUp');
const mobileSignIn = document.getElementById('mobileSignIn');


// ===================================
// AUTHENTICATION PANEL SWITCHING
// ===================================

function showSignUp() {
    container.classList.add('right-panel-active');
    sessionStorage.setItem('authPanel', 'signup');
}

function showSignIn() {
    container.classList.remove('right-panel-active');
    sessionStorage.setItem('authPanel', 'signin');
}


// Desktop buttons

if (signUpButton) {
    signUpButton.addEventListener('click', showSignUp);
}

if (signInButton) {
    signInButton.addEventListener('click', showSignIn);
}


// Mobile buttons

if (mobileSignUp) {
    mobileSignUp.addEventListener('click', showSignUp);
}

if (mobileSignIn) {
    mobileSignIn.addEventListener('click', showSignIn);
}


// ===================================
// RESTORE FORM DATA
// ===================================

const formDataElement = document.getElementById('form-data');

const formData = formDataElement
    ? JSON.parse(formDataElement.textContent)
    : {};


// ===================================
// DYNAMIC CATEGORY FIELDS
// ===================================

const categorySelect = document.getElementById('category');

const categoryContainer = document.getElementById(
    'category-fields'
);

const categoryFieldsElement = document.getElementById(
    'category-fields-data'
);

const categoryFieldsData = categoryFieldsElement
    ? JSON.parse(categoryFieldsElement.textContent)
    : {};


function showCategoryFields() {

    if (!categorySelect || !categoryContainer) {
        return;
    }

    const selectedCategory = categorySelect.value;

    categoryContainer.innerHTML = '';

    const fields = categoryFieldsData[selectedCategory] || [];

    if (fields.length === 0) {
        return;
    }

    // Section heading

    const heading = document.createElement('h6');

    heading.textContent = 'Additional Details (Optional)';

    categoryContainer.appendChild(heading);


    // Generate configured fields

    fields.forEach(field => {

        const wrapper = document.createElement('div');

        wrapper.className = 'category-field';


        const label = document.createElement('label');

        label.textContent = field.label;

        label.htmlFor = `category_${field.key}`;


        let input;

        if (field.type === 'textarea') {

            input = document.createElement('textarea');

            input.rows = 3;

        } else {

            input = document.createElement('input');

            input.type = ['text', 'number', 'date'].includes(field.type)
                ? field.type
                : 'text';
        }


        input.name = field.key;

        input.id = `category_${field.key}`;

        input.className = 'form-control';

        input.required = false;


        // Restore previously submitted values

        if (formData[field.key] !== undefined) {

            input.value = formData[field.key];

        }


        wrapper.appendChild(label);

        wrapper.appendChild(input);

        categoryContainer.appendChild(wrapper);

    });

}


// Category change listener

if (categorySelect) {

    categorySelect.addEventListener(
        'change',
        showCategoryFields
    );


    // Restore selected category

    if (formData.category) {

        categorySelect.value = formData.category;

    }


    // Display fields on page load

    showCategoryFields();

}


// ===================================
// RESTORE NORMAL SIGNUP INPUTS
// ===================================

document.querySelectorAll('.sign-up-container input').forEach(input => {

    if (
        input.type !== 'password' &&
        formData[input.name] !== undefined
    ) {

        input.value = formData[input.name];

    }

});


// Restore gender selection

const genderSelect = document.getElementById('gender');

if (genderSelect && formData.gender) {

    genderSelect.value = formData.gender;

}


// ===================================
// RESTORE AUTHENTICATION PANEL
// ===================================

const initialPanel = container.dataset.initialPanel;

if (initialPanel === 'signin') {

    showSignIn();

} else if (initialPanel === 'signup') {

    showSignUp();

} else if (sessionStorage.getItem('authPanel') === 'signup') {

    showSignUp();

} else {

    showSignIn();

}


// ===================================
// PASSWORD SHOW / HIDE
// ===================================

document.querySelectorAll('.password-field').forEach(wrapper => {

    const password = wrapper.querySelector('input');

    const toggler = wrapper.querySelector('i');

    if (!password || !toggler) {
        return;
    }

    toggler.addEventListener('click', () => {

        const isPassword = password.type === 'password';

        password.type = isPassword ? 'text' : 'password';

        toggler.classList.toggle(
            'fa-eye-slash',
            isPassword
        );

        toggler.classList.toggle(
            'fa-eye',
            !isPassword
        );

    });

});
