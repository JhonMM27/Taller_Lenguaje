from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def login_page(request):
    if request.user.is_authenticated:
        return redirect('reportes:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Email y contraseña son requeridos')
            return render(request, 'login.html')

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            messages.error(request, 'Credenciales inválidas')
            return render(request, 'login.html')

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'reportes:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Credenciales inválidas')
            return render(request, 'login.html')

    return render(request, 'login.html')


@login_required
def logout_page(request):
    logout(request)
    return redirect('usuarios:login')