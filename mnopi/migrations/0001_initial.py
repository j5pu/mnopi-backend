# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserCategory'
        db.create_table('user_categories', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('taxonomy', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal(u'mnopi', ['UserCategory'])

        # Adding model 'User'
        db.create_table('users', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'mnopi', ['User'])

        # Adding M2M table for field groups on 'User'
        m2m_table_name = db.shorten_name('users_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm[u'mnopi.user'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['user_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'User'
        m2m_table_name = db.shorten_name('users_user_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(orm[u'mnopi.user'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['user_id', 'permission_id'])

        # Adding model 'CategorizedDomain'
        db.create_table('domains', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=500)),
        ))
        db.send_create_signal(u'mnopi', ['CategorizedDomain'])

        # Adding M2M table for field categories on 'CategorizedDomain'
        m2m_table_name = db.shorten_name('domains_categories')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('categorizeddomain', models.ForeignKey(orm[u'mnopi.categorizeddomain'], null=False)),
            ('usercategory', models.ForeignKey(orm[u'mnopi.usercategory'], null=False))
        ))
        db.create_unique(m2m_table_name, ['categorizeddomain_id', 'usercategory_id'])

        # Adding model 'UserCategorization'
        db.create_table('user_categorization', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mnopi.User'])),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mnopi.UserCategory'])),
            ('weigh', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'mnopi', ['UserCategorization'])

        # Adding model 'PageVisited'
        db.create_table('pages_visited', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mnopi.User'])),
            ('page_visited', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('domain', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mnopi.CategorizedDomain'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'mnopi', ['PageVisited'])

        # Adding model 'Client'
        db.create_table(u'mnopi_client', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('allowed', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'mnopi', ['Client'])

        # Adding model 'Search'
        db.create_table('searches', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('search_query', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('search_results', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mnopi.User'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mnopi.Client'])),
        ))
        db.send_create_signal(u'mnopi', ['Search'])

        # Adding model 'ClientSession'
        db.create_table('client_sessions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mnopi.User'])),
            ('expiration_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 4, 17, 0, 0))),
            ('session_key', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mnopi.Client'])),
        ))
        db.send_create_signal(u'mnopi', ['ClientSession'])


    def backwards(self, orm):
        # Deleting model 'UserCategory'
        db.delete_table('user_categories')

        # Deleting model 'User'
        db.delete_table('users')

        # Removing M2M table for field groups on 'User'
        db.delete_table(db.shorten_name('users_groups'))

        # Removing M2M table for field user_permissions on 'User'
        db.delete_table(db.shorten_name('users_user_permissions'))

        # Deleting model 'CategorizedDomain'
        db.delete_table('domains')

        # Removing M2M table for field categories on 'CategorizedDomain'
        db.delete_table(db.shorten_name('domains_categories'))

        # Deleting model 'UserCategorization'
        db.delete_table('user_categorization')

        # Deleting model 'PageVisited'
        db.delete_table('pages_visited')

        # Deleting model 'Client'
        db.delete_table(u'mnopi_client')

        # Deleting model 'Search'
        db.delete_table('searches')

        # Deleting model 'ClientSession'
        db.delete_table('client_sessions')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'mnopi.categorizeddomain': {
            'Meta': {'object_name': 'CategorizedDomain', 'db_table': "'domains'"},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mnopi.UserCategory']", 'symmetrical': 'False'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'mnopi.client': {
            'Meta': {'object_name': 'Client'},
            'allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'client_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'mnopi.clientsession': {
            'Meta': {'object_name': 'ClientSession', 'db_table': "'client_sessions'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mnopi.Client']"}),
            'expiration_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 4, 17, 0, 0)'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mnopi.User']"})
        },
        u'mnopi.pagevisited': {
            'Meta': {'object_name': 'PageVisited', 'db_table': "'pages_visited'"},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mnopi.CategorizedDomain']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page_visited': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mnopi.User']"})
        },
        u'mnopi.search': {
            'Meta': {'object_name': 'Search', 'db_table': "'searches'"},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mnopi.Client']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'search_query': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'search_results': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mnopi.User']"})
        },
        u'mnopi.user': {
            'Meta': {'object_name': 'User', 'db_table': "'users'"},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mnopi.UserCategory']", 'through': u"orm['mnopi.UserCategorization']", 'symmetrical': 'False'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'mnopi.usercategorization': {
            'Meta': {'object_name': 'UserCategorization', 'db_table': "'user_categorization'"},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mnopi.UserCategory']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mnopi.User']"}),
            'weigh': ('django.db.models.fields.IntegerField', [], {})
        },
        u'mnopi.usercategory': {
            'Meta': {'object_name': 'UserCategory', 'db_table': "'user_categories'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'taxonomy': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['mnopi']