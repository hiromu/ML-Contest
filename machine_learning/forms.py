# -*- coding: utf-8 -*-

from django.forms import CharField, ChoiceField, ModelForm

from machine_learning.models import Problem, Submission

class ProblemForm(ModelForm):
    type = ChoiceField(label = u'スコア計算方法', choices = ((0, '完全一致 [正解数 * 係数]'), (1, '差分 [((閾値 - 差分) * 係数)の総和]')))

    class Meta:
        model = Problem
        exclude = ('user', 'size')

    def __init__(self, *args, **kwargs):
        super(ProblemForm, self).__init__(*args, **kwargs)

        self.fields['score'].required = False
        self.fields['score'].widget.attrs['readonly'] = True
        self.fields['threshold'].required = False

    def clean(self, *args, **kwargs):
        cleaned_data = super(ProblemForm, self).clean(*args, **kwargs)

        type = cleaned_data.get('type')
        count = cleaned_data.get('count')
        coefficient = cleaned_data.get('coefficient')

        if type == u'0':
            cleaned_data['threshold'] = 0
            cleaned_data['score'] = count * coefficient
        elif type == u'1':
            threshold = cleaned_data.get('threshold')
            if not threshold:
                self._errors['threshold'] = self.error_class(['このフィールドは必須です。'])
                del cleaned_data['threshold']
            else:
                cleaned_data['score'] = count * threshold * coefficient

        testdata = cleaned_data.get('testdata')
        if testdata:
            size = sum([1 for i in testdata])
            if size < count:
                self._errors['count'] = self.error_class(['テストデータの数より小さいか等しい必要があります。'])
                del cleaned_data['count']

        return cleaned_data

class ProblemEditForm(ModelForm):
    class Meta:
        model = Problem
        fields = ('name', 'statement')

class ProblemDeleteForm(ModelForm):
    class Meta:
        model = Problem
        fields = ()

class SubmissionForm(ModelForm):
    class Meta:
        model = Submission
        fields = ('data', 'source')
