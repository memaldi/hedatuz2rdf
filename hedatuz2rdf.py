# coding=iso-8859-15
from rdflib import Graph, Literal
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.common import Metadata
import urllib2, urllib
import simplejson
from urlparse import urlparse

#Creator class, used to store the name, the viaf_url (if any) and an unique id
class Creator:
    def __init__(self, name, id, viaf_id=None):
        self.name = name
        self.viaf_id = viaf_id
        self.id = id

#Constants
HEDATUZ_URL = 'http://hedatuz.euskomedia.org/cgi/oai2'
VIAF_URL = 'http://viaf.org/viaf/'
RDF_DOMAIN = u'http://helheim.deusto.es/'
CREATOR_ID_DIGITS = 5
        
def main():
    #RDF graph initialization
    g = Graph()
    g.bind("dc", "http://purl.org/dc/elements/1.1/")
    g.bind("bibo", "http://purl.org/ontology/bibo/")
    g.bind("foaf", "http://xmlns.com/foaf/0.1/")
    g.bind("owl", "http://www.w3.org/2002/07/owl#")
    
    #OAI2 access initialization
    registry = MetadataRegistry()
    registry.registerReader('oai_dc', oai_dc_reader)
    client = Client(HEDATUZ_URL, registry)
    
    creator_dict = {}
    creator_id_count = 1
    
    #print dir(client.listRecords)
    
    #Iterate over each record in headatuz database
    for record in client.listRecords(metadataPrefix='oai_dc'):
        for item in record:
            if type(item) == Metadata:
                item_dict = dict(item.getMap())
                ##print item_dict
                record_creator_list = []
                creator_list = item_dict['creator']
                #Get record identifier
                record_id_url = urlparse(item_dict['identifier'][0])
                record_id = record_id_url.path.replace('/', '')
                #Iterate over each creator of the current record
                for creator in creator_list:
                    creator_orig = creator                    
                    if creator_orig not in creator_dict.keys():
                        creator = creator.replace(' ', '%20')
                        creator_params = urllib.urlencode({'query': creator.encode('utf-8')})
                        req = urllib2.Request('http://viaf.org/viaf/AutoSuggest?' + creator_params)
                        f = urllib2.urlopen(req)
                        try:
                            json_item = simplejson.load(f, strict=False)
                        except Exception as e:
                            print e
                            break
                        #Generate creator id
                        #id_len = len(str(creator_id_count))
                        #digits = CREATOR_ID_DIGITS - id_len
                        #id_formatter = '%0' + str(digits) + 'd'
                        creator_id = creator_id_count
                        creator_id_count = creator_id_count + 1
                        
                        #Get results from VIAF (if any)
                        if json_item['result']:
                            viaf_id = json_item['result'][0]['viafid']
                            
                            #Create new Creator instance
                            creator = Creator(creator_orig, creator_id, viaf_id)
                        else:
                            #Create new Creator instance
                            creator = Creator(creator_orig, creator_id)
                        creator_dict[creator_orig] = creator
                        record_creator_list.append(creator)
                    else:
                        record_creator_list.append(creator_dict[creator_orig])
                
                item_dict['creator'] = record_creator_list
                item_type_list = item_dict['type']
                if type(item_type_list) == list:
                    for item_type in item_type_list:
                        if item_type.encode('utf-8') == 'Artículo':
                            #print 'Articulo'
                            g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/Article'))
                        elif item_type.encode('utf-8') == 'Sección de Libro':
                            #print 'Seccion'
                            g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/BookSection'))
                        elif item_type == u'Libro':
                            #print 'Libro'
                            g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/Book'))
                        elif item_type == u'PeerReviewed':
                            #print 'Peer'
                            g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://purl.org/ontology/bibo/DocumentStatus', u'http://purl.org/ontology/bibo/status/peerReviewed'))

                else:
                    item_type = item_dict['type']
                    if item_type.encode('utf-8') == 'Artículo':
                        #print 'Articulo'
                        g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/Article'))
                    elif item_type.encode('utf-8') == 'Sección de Libro':
                        #print 'Seccion'
                        g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/BookSection'))
                    elif item_type == u'Libro':
                        #print 'Libro'
                        g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/Book'))
                    elif item_type == u'PeerReviewed':
                        #print 'Peer'
                        g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://purl.org/ontology/bibo/DocumentStatus', u'http://purl.org/ontology/bibo/status/peerReviewed'))
                
                for key in item_dict:
                    obj = item_dict[key]
                    if type(obj) == list:
                        for creator_item in obj:
                            if key == 'creator':
                                g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://purl.org/dc/elements/1.1/creator', RDF_DOMAIN + u'resource/author/' + str(creator_item.id)))
                            else:
                                g.add((RDF_DOMAIN + u'resource/biblio/' + record_id, u'http://purl.org/dc/elements/1.1/' + key, Literal(creator_item)))
                                
    for key in creator_dict.keys():
        creator = creator_dict[key]
        g.add((RDF_DOMAIN + u'resource/author/' + str(creator.id), u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://xmlns.com/foaf/0.1/Person'))
        g.add((RDF_DOMAIN + u'resource/author/' + str(creator.id), u'http://xmlns.com/foaf/0.1/name', Literal(creator.name)))
        if creator.viaf_id != None:
            g.add((RDF_DOMAIN + u'resource/author/' + str(creator.id), u'http://www.w3.org/2002/07/owl#sameAs', VIAF_URL + creator.viaf_id))
                                
    print len(g)

    #for s, p, o in g:
        ##print s, p, o

    f = open('hedatuz.rdf', 'w')
    f.write(g.serialize(format='pretty-xml'))
    g.close()
    f.close()

if __name__ == "__main__":
    main()
        
