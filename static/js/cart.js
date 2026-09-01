var updateBtns = document.getElementsByClassName('update-cart')

for (var i = 0; i < updateBtns.length; i++) {

    updateBtns[i].addEventListener('click', function () {

        var productId = this.dataset.product
        var action = this.dataset.action

        console.log('productId:', productId, 'Action:', action)
        console.log('USER:', user)

        if (user == 'AnonymousUser') {
            addCookieItem(productId, action)
        } else {
            updateUserOrder(productId, action)
        }

    })
}


// SUCCESS MESSAGE FUNCTION
function showSuccessMessage() {

    var message = document.getElementById('success-message')

    message.style.display = 'block'

    setTimeout(function () {
        message.style.display = 'none'
    }, 2000)
}


// GUEST USER CART
function addCookieItem(productId, action) {

    console.log('User is not authenticated')

    if (action == 'add') {

        if (cart[productId] == undefined) {
            cart[productId] = {'quantity': 1}

        } else {
            cart[productId]['quantity'] += 1
        }

        // Show success message
        showSuccessMessage()
    }


    if (action == 'remove') {

        cart[productId]['quantity'] -= 1

        if (cart[productId]['quantity'] <= 0) {
            console.log('Item should be deleted')
            delete cart[productId]
        }
    }


    console.log('CART:', cart)

    document.cookie = 'cart=' + JSON.stringify(cart) + ";domain=;path=/"


    // Wait so user can see the message
    if (action == 'add') {

        setTimeout(function () {
            location.reload()
        }, 2000)

    } else {

        location.reload()
    }

} // ← closes addCookieItem function


// AUTHENTICATED USER CART
function updateUserOrder(productId, action) {

    console.log('User is authenticated, sending data...')

    var url = '/update_item/'

    fetch(url, {
        method: 'POST',

        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },

        body: JSON.stringify({
            'productId': productId,
            'action': action
        })
    })

    .then((response) => {
        return response.json()
    })

    .then((data) => {

        // Show message only when adding product
        if (action == 'add') {

            showSuccessMessage()

            // Wait 2 seconds before reload
            setTimeout(function () {
                location.reload()
            }, 2000)

        } else {

            location.reload()
        }

    }) // ← closes .then()

} // ← closes updateUserOrder function


