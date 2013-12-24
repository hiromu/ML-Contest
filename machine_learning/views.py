# -*- coding: utf-8 -*-

import csv
import random
import datetime
import StringIO

from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render_to_response, RequestContext

from machine_learning.forms import ProblemForm, ProblemDeleteForm, ProblemEditForm, SubmissionForm
from machine_learning.models import Problem, Submission
from machine_learning.settings import TIMEOUT

def index(request):
    problems = Problem.objects.all().order_by('id')
    submissions = Submission.objects.values('problem').annotate(max = Max('score'))

    table = {}
    for problem in problems:
        table[problem.id] = problem
    for submission in submissions:
        table[submission['problem']].max = submission['max']

    context = {'problems': map(lambda x: x[1], sorted(table.items()))}
    return render_to_response('index.html', context, RequestContext(request))

def ranking(request):
    ranking = Submission.objects.values('problem', 'user').annotate(max = Max('score'))
    problems = Problem.objects.all().order_by('id')
    users = User.objects.filter(is_staff = False).order_by('id')

    table = {}
    name = {}
    for user in users:
        table[user.id] = {}
        name[user.id] = user.last_name + ' ' + user.first_name
        for problem in problems:
            table[user.id][problem.id] = 0.0
    for rank in ranking:
        if rank['user'] in table:
            table[rank['user']][rank['problem']] = rank['max']

    total = {}
    for user in users:
        total[user.id] = sum(table[user.id].values())

    ranking = []
    for index, (key, value) in enumerate(sorted(table.items(), key = lambda x: total[x[0]], reverse = True)):
        if index != 0 and ranking[-1][-1] == total[key]:
            rank = ranking[-1][0]
        else:
            rank = index + 1

        ranking.append([rank, name[key]])
        for problem, score in sorted(value.items()):
            ranking[-1].append(score)
        ranking[-1].append(total[key])

    context = {'problems': problems, 'ranking': ranking}
    return render_to_response('ranking.html', context, RequestContext(request))

@login_required
def create(request):
    if not request.user.is_staff:
        return redirect('machine_learning.views.index')

    if request.method == 'POST':
        form = ProblemForm(request.POST, request.FILES)
        if form.is_valid():
            problem = form.save(commit = False)
            problem.size = sum([1 for i in problem.testdata])
            problem.save()
            return redirect('machine_learning.views.view', problem.id)
    else:
        form = ProblemForm()

    context = {'form': form}
    return render_to_response('create.html', context, RequestContext(request))

@login_required
def delete(request, problem_id):
    if not request.user.is_staff:
        return redirect('machine_learning.views.index')

    problem = get_object_or_404(Problem, pk = problem_id)
    if request.method == 'POST':
        form = ProblemDeleteForm(request.POST)
        if form.is_valid():
            problem.delete()
            return redirect('machine_learning.views.index')
    else:
        form = ProblemDeleteForm()

    context = {'form': form, 'problem': problem}
    return render_to_response('delete.html', context, RequestContext(request))

@login_required
def download(request, problem_id):
    problem = get_object_or_404(Problem, pk = problem_id)
    testcase = []

    submission = get_submission(problem, request.user)
    if submission:
        testcase = map(int, submission.testcase.split(','))

    if len(testcase) == 0:
        testcase = range(problem.size)
        random.shuffle(testcase)
        testcase = testcase[:problem.count]

        submission = Submission(problem = problem, user = request.user, testcase = ','.join(map(str, testcase)), datetime = datetime.datetime.now())
        submission.save()

    testdata = {}
    for i, line in enumerate(csv.reader(problem.testdata)):
        if i in testcase:
            testdata[i] = line[:-1]

    output = StringIO.StringIO()
    writer = csv.writer(output)
    for i in testcase:
        writer.writerow(testdata[i])

    return HttpResponse(output.getvalue(), mimetype = 'application/octet-stream')

@login_required
def edit(request, problem_id):
    if not request.user.is_staff:
        return redirect('machine_learning.views.index')

    problem = get_object_or_404(Problem, pk = problem_id)
    if request.method == 'POST':
        form = ProblemEditForm(request.POST, instance = problem)
        if form.is_valid():
            problem = form.save()
            return redirect('machine_learning.views.view', problem.id)
    else:
        form = ProblemEditForm(instance = problem)

    context = {'form': form, 'problem': problem}
    return render_to_response('edit.html', context, RequestContext(request))

@login_required
def timer(request, problem_id):
    problem = get_object_or_404(Problem, pk = problem_id)
    submission = get_submission(problem, request.user)
    if submission:
        timeout = submission.datetime + datetime.timedelta(seconds = TIMEOUT)
        return HttpResponse(timeout.strftime('%Y/%m/%d %H:%M:%S %z'))
    return HttpResponse()

@login_required
def user(request, user_id):
    user = get_object_or_404(User, pk = user_id)
    submissions = Submission.objects.filter(user = user).exclude(data = '').order_by('-datetime')[:100]
    context = {'request_user': user, 'submissions': submissions}
    return render_to_response('user.html', context, RequestContext(request))

@login_required
def view(request, problem_id):
    problem = get_object_or_404(Problem, pk = problem_id)
    error = ''
    
    if request.method == 'POST':
        submission = get_submission(problem, request.user)
        if submission:
            form = SubmissionForm(request.POST, request.FILES, instance = submission)
            if form.is_valid():
                submission = form.save(commit = False)
                testcase = map(int, submission.testcase.split(','))

                answer = {}
                for i, line in enumerate(csv.reader(problem.testdata)):
                    if i in testcase:
                        answer[i] = line[-1]

                score = 0
                if problem.type == 0:
                    for i, data in zip(testcase, submission.data):
                        if str(answer[i]).lower() == data.strip().lower():
                            score += 1
                elif problem.type == 1:
                    for i, data in zip(testcase, submission.data):
                        try:
                            diff = abs(float(answer[i]) - float(data.strip()))
                            score += max(problem.threshold - diff, 0)
                        except ValueError:
                            pass

                submission.score = score * problem.coefficient
                submission.save()
                return redirect('machine_learning.views.user', request.user.id)
        else:
            error = '時間切れです。'
            form = SubmissionForm()
    else:
        form = SubmissionForm()

    context = {'error': error, 'form': form, 'problem': problem}
    return render_to_response('view.html', context, RequestContext(request))

def get_submission(problem, user):
    submission = Submission.objects.filter(problem = problem, user = user, data = '').order_by('-datetime')[:1]
    if not submission:
        return None

    delta = datetime.datetime.utcnow() - submission[0].datetime.replace(tzinfo = None)
    if delta.days * 86400 + delta.seconds > TIMEOUT:
        return None

    return submission[0]
