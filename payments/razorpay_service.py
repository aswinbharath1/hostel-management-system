import razorpay
from django.conf import settings


def get_razorpay_client():
    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

def create_razorpay_order(amount, fee_id):
    client = get_razorpay_client()

    order_data = {
        'amount': int(amount * 100),
        'currency': 'INR',
        'receipt': f'fee_{fee_id}',
    }

    order = client.order.create(data=order_data)

    return order