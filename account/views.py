import datetime
from django.shortcuts import render, redirect
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django_htmx.http import retarget, HttpResponseClientRedirect, HttpResponseClientRefresh

from .models import UserToken
from .utils import send_reset_email_thread, generate_token


@login_not_required
@require_http_methods(["GET", "POST"])
def register(request):

	if request.htmx and request.POST:
		username = request.POST['username'].strip()
		email = request.POST['email'].strip()
		password = request.POST['password'].strip()
		confirm_password = request.POST['confirm_password'].strip()

		if not username:
			response = HttpResponse("Username is required", status=400)               
			return retarget(response, '#danger-username')

		if not email:
			response = HttpResponse("Email is required", status=400)               
			return retarget(response, '#danger-email')

		if not password:
			response = HttpResponse("Password is required", status=400)               
			return retarget(response, '#danger-password')

		if not password == confirm_password:
			response = HttpResponse("Confirm pasword not matching", status=400)               
			return retarget(response, '#danger-confirm-password')

		if User.objects.filter(username=username).exists():
			response = HttpResponse("User name taken", status=409)               
			return retarget(response, '#danger-username')
			
		if User.objects.filter(email=email).exists():
			response = HttpResponse("Email already exists", status=409)               
			return retarget(response, '#danger-email')
            
		user = User.objects.create_user(username=username, email=email, password=password)
		user.is_active = False 
		user.save()

		verify_token = generate_token()
		expiration_date = timezone.now() + datetime.timedelta(minutes=10)
		user_token = UserToken.objects.create(user=user, token=verify_token, expiration_date=expiration_date)
		user_token.save()

		url = f'{settings.DOMAIN}/accounts/verify-account'
		message = 'email/verify_account_email.html'
		subject = 'Account Verification'
		send_reset_email_thread(email, verify_token, url, message, subject)

		messages.success(request, 'Registered Successfully! Check your mail & verify')
		return HttpResponseClientRedirect('/accounts/login')
		   
	return render(request, 'pages/auth/register.html')


@login_not_required
@require_GET
def verify_account(request, token):

	user_token = UserToken.objects.filter(token=token).first()

	if not user_token:
		response = "Invalid or expired token"
		context = {'message': response}               
		return render(request, 'pages/auth/verify_account.html', context)

	user = user_token.user
	user.is_active = True
	user.save()
	user_token.mark_as_used()
	
	context = {
    	'user': user,
    	'message': "Account verified successfully!",
	}
	return render(request, 'pages/auth/verify_account.html', context)


@login_not_required
@require_http_methods(["GET", "POST"])
def login(request):

	if request.htmx and request.POST:
		username = request.POST['username'].strip()
		password = request.POST['password'].strip()

		if not username:
			response = HttpResponse("Username is required", status=400)               
			return retarget(response, '#danger-username')

		if not password:
			response = HttpResponse("Password is required", status=400)               
			return retarget(response, '#danger-password')

		if not User.objects.filter(username=username).exists():
			response = HttpResponse("Username not exists", status=404)               
			return retarget(response, '#danger-username')

		if not User.objects.filter(username=username, is_active=True).exists():
			response = HttpResponse("Account not verified, check your mail", status=403)               
			return retarget(response, '#danger-username')

		user = auth.authenticate(username=username, password=password)

		if user is None:
			response = HttpResponse("Re-check the password", status=401)               
			return retarget(response, '#danger-password')

		auth.login(request, user)
		return HttpResponseClientRedirect('/')
       
	return render(request, 'pages/auth/login.html')


@require_GET
def logout(request):

    auth.logout(request)
    return redirect('login')


@login_not_required
@require_http_methods(["GET", "POST"])
def forgot_password(request):

	if request.htmx and request.POST:
		email = request.POST['email']
		user = User.objects.filter(email=email).first()

		if user is None:
			response = HttpResponse("Email not found", status=404)               
			return retarget(response, '#danger-email')

		reset_token = generate_token()
		expiration_date = timezone.now() + datetime.timedelta(minutes=10)
		user_token = UserToken.objects.create(user=user, token=reset_token, expiration_date=expiration_date)
		user_token.save()

		url = f'{settings.DOMAIN}/accounts/reset-password'
		message = 'email/reset_password_email.html'
		subject = 'Password Reset'
		send_reset_email_thread(email, reset_token, url, message, subject)

		response = HttpResponse("Email Sent!", status=200)               
		return retarget(response, '#email-button')

	return render(request, 'pages/auth/forget_password.html')


@login_not_required
@require_http_methods(["GET", "POST"])
def reset_password(request, token):

	if request.htmx and request.POST:
		password = request.POST['password'].strip()
		confirm_password = request.POST['confirm_password'].strip()

		user_token = UserToken.objects.filter(token=token).first()

		if not user_token:
			messages.warning(request, 'Invalid or expired token')
			return HttpResponseClientRefresh()

		if user_token.user.check_password(password):
			response = HttpResponse("New password cannot be the same as the old password", status=400)
			return retarget(response, '#danger-password')

		if not password:
			response = HttpResponse("Password is required", status=400)               
			return retarget(response, '#danger-password')

		if not password == confirm_password:
			response = HttpResponse("Confirm pasword not matching", status=400)               
			return retarget(response, '#danger-confirm-password')

		user = user_token.user
		user.set_password(password)
		user.save()
		user_token.mark_as_used()
		
		messages.success(request, 'Password reset successfully 👍')
		return HttpResponseClientRedirect('/accounts/login')

	context = {"token": token}
	return render(request, 'pages/auth/reset_password.html', context)


@require_http_methods(["POST"])
def delete_account(request):

	user = request.user

	if request.htmx and request.POST:
		username = request.POST['username'].strip()

		if username == user.username:
			user.delete()
			return HttpResponseClientRedirect('/')

		response = HttpResponse("Enter your correct username", status=400)               
		return retarget(response, '#danger-username')