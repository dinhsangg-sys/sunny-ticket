import copy
import json
from django.test import TestCase
from django.contrib.auth.models import Permission
from apps.accounts.models import User
from .models import Workspace
from .ticket_lifecycle import enforce_ticket_lifecycle,ticket_used

class TicketDeletionTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_superuser('root',password='test-password')
        self.client.force_login(self.user)
        self.data={'ticketTypes':[{'id':'eco','name':'Eco','active':True},{'id':'unused','name':'Unused','active':True}], 'bookings':[{'id':'b1','ticketId':'eco','ticketType':'Eco'}]}
        Workspace.objects.create(pk=1,data=self.data)

    def put(self,data):
        return self.client.put('/api/state/',json.dumps({'data':data,'revision':Workspace.objects.get(pk=1).revision}),content_type='application/json')

    def test_unused_ticket_can_be_deleted(self):
        data=copy.deepcopy(self.data);data['ticketTypes'].pop()
        self.assertEqual(self.put(data).status_code,200)
        self.assertEqual(len(Workspace.objects.get(pk=1).data['ticketTypes']),1)

    def test_used_ticket_cannot_be_deleted_even_with_references_removed(self):
        data=copy.deepcopy(self.data);data['ticketTypes'].pop(0);data['bookings']=[]
        self.assertEqual(self.put(data).status_code,400)
        self.assertEqual(Workspace.objects.get(pk=1).revision,0)

    def test_stop_used_ticket_keeps_history(self):
        data=copy.deepcopy(self.data);data['ticketTypes'][0]['active']=False
        self.assertEqual(self.put(data).status_code,200)
        stored=Workspace.objects.get(pk=1).data
        self.assertEqual(stored['bookings'],self.data['bookings'])
        self.assertTrue(stored['ticketTypes'][0]['hasActivity'])

    def test_activity_remains_after_reference_deleted(self):
        data=copy.deepcopy(self.data);data['bookings']=[]
        self.assertEqual(self.put(data).status_code,200)
        stored=Workspace.objects.get(pk=1).data;stored['ticketTypes'][0]['hasActivity']=False;stored['ticketTypes'].pop(0)
        self.assertEqual(self.put(stored).status_code,400)

    def test_all_reference_types_protect_ticket(self):
        for key in ('bookings','agentPrices','costPrices','priceListItems'):
            for ref in ({'ticketId':'eco'},{'ticketCode':'eco'},{'ticketType':'Eco'}):
                self.assertTrue(ticket_used({key:[ref]},self.data['ticketTypes'][0]))
        self.assertFalse(ticket_used({'bookings':[{'ticketId':'other','ticketType':'Eco'}]},self.data['ticketTypes'][0]))

    def test_restricted_delete_checks_permission_and_usage(self):
        self.user.is_superuser=False;self.user.role='operator';self.user.save()
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='legacy',codename__in=['ticket_type__view','ticket_type__delete']))
        response=self.client.get('/api/operations/').json()
        rows=response['resources']['ticketTypes']['rows']
        self.assertFalse(rows[0]['_deletable']);self.assertTrue(rows[1]['_deletable'])
        def delete(index):return self.client.post('/api/operations/',json.dumps({'action':'delete','resource':'ticketTypes','index':index,'revision':0}),content_type='application/json')
        self.assertEqual(delete(0).status_code,400)
        self.assertEqual(delete(1).status_code,200)
