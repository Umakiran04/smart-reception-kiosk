<!DOCTYPE html>
<html>
<head>
    <title>Aadhaar Verification</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>

<body class="light-body">

    <!-- ✅ FIX: action points to /csif -->
    <form class="card" method="POST" action="/csif">
        <h2>Aadhaar Verification</h2>

        <p class="subtitle">
            Please enter your Aadhaar details to continue
        </p>

        <p style="font-size:12px;color:#666;margin-top:-10px;">
            Aadhaar details are used only for visitor verification
        </p>

        <!-- ❌ ERROR MESSAGE -->
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}

        <!-- ✅ SUCCESS MESSAGE -->
        {% if success %}
            <div class="success">
                ✅ Aadhaar verified successfully<br>
                Welcome, <strong>{{ name }}</strong>
            </div>
        {% endif %}

        <input
            type="text"
            name="aadhaar"
            placeholder="Enter 12-digit Aadhaar"
            maxlength="12"
            inputmode="numeric"
            pattern="[0-9]{12}"
            required
        >

        <!-- ✅ type=date sends YYYY-MM-DD (perfect for backend) -->
        <input
            type="date"
            name="dob"
            required
        >

        <button class="btn btn-blue full-width" type="submit">
            Verify & Continue
        </button>
    </form>

</body>
</html>
