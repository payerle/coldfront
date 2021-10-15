# Generated by Django 2.2.24 on 2021-10-15 19:19

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=512, null=True, unique=True)),
                ('level', models.IntegerField(help_text='The lower this value, the higher this type is in the organization.', unique=True)),
                ('parent', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='organization.OrganizationLevel')),
            ],
            options={
                'ordering': ['-level'],
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('code', models.CharField(help_text='A short code for referencing this organization.  Typically will be combined with short codes from all parents to get an unique reference. May not contain hyphen (-)', max_length=512, null=True, validators=[django.core.validators.RegexValidator(inverse_match=True, message='Code field may not contain hyphen (-)', regex='-')])),
                ('shortname', models.CharField(help_text='A medium length name for this organization, used in many displays.', max_length=1024, null=True)),
                ('longname', models.CharField(help_text='The full name for this organization, for official contexts', max_length=2048, null=True)),
                ('is_selectable_for_user', models.BooleanField(default=True, help_text='This organization can be selected for Users')),
                ('is_selectable_for_project', models.BooleanField(default=True, help_text='This organization can be selected for Projects')),
                ('organization_level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organization.OrganizationLevel')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='organization.Organization')),
            ],
            options={
                'ordering': ['organization_level', 'code'],
            },
        ),
        migrations.CreateModel(
            name='Directory2Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('directory_string', models.CharField(max_length=1024, unique=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organization.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.UniqueConstraint(fields=('code', 'parent'), name='organization_code_parent_unique'),
        ),
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.UniqueConstraint(condition=models.Q(parent__isnull=True), fields=('code',), name='organization_code_nullparent_unique'),
        ),
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.UniqueConstraint(fields=('shortname', 'parent'), name='organization_shortname_parent_unique'),
        ),
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.UniqueConstraint(condition=models.Q(parent__isnull=True), fields=('shortname',), name='organization_shortname_nullparent_unique'),
        ),
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.UniqueConstraint(fields=('longname', 'parent'), name='organization_longname_parent_unique'),
        ),
        migrations.AddConstraint(
            model_name='organization',
            constraint=models.UniqueConstraint(condition=models.Q(parent__isnull=True), fields=('longname',), name='organization_longname_nullparent_unique'),
        ),
    ]
