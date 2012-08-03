# coding=iso-8859-15
from rdflib import Graph
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.common import Metadata
import urllib2, urllib
import simplejson

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
    
    #OAI2 access initialization
    registry = MetadataRegistry()
    registry.registerReader('oai_dc', oai_dc_reader)
    client = Client(HEDATUZ_URL, registry)
    
    creator_dict = {}
    creator_id_count = 1
    
    #Iterate over each record in headatuz database
    for record in client.listRecords(metadataPrefix='oai_dc'):
        for item in record:
            if type(item) == Metadata:
                item_dict = dict(item.getMap())
                record_creator_list = []
                creator_list = item_dict['creator']
                #Iterate over each creator of the current record
                for creator in creator_list:
                    creator_orig = creator
                    creator = creator.replace(' ', '%20')
                    creator_params = urllib.urlencode({'query': creator.encode('utf-8')})
                    req = urllib2.Request('http://viaf.org/viaf/AutoSuggest?' + creator_params)
                    f = urllib2.urlopen(req)
                    json_item = simplejson.load(f, strict=False)
                    
                    if creator_orig not in creator_dict.keys():
                        #Generate creator id
                        id_len = len(str(creator_id_count))
                        digits = CREATOR_ID_DIGITS - int(id_len)
                        id_formatter = '%0' + str(digits) + 'd'
                        creator_id = id_formatter % creator_id_count
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
                            print 'Articulo'
                            g.add((DOMINIO + u'resource/biblio/' + viaf_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/Article'))
                        elif item_type.encode('utf-8') == 'Sección de Libro':
                            print 'Seccion'
                            g.add((DOMINIO + u'resource/biblio/' + viaf_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/BookSection'))
                        elif item_type == u'Libro':
                            print 'Libro'
                            g.add((DOMINIO + u'resource/biblio/' + viaf_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/Book'))
                        elif item_type == u'PeerReviewed':
                            print 'Peer'
                            g.add((DOMINIO + u'resource/biblio/' + viaf_id, u'http://purl.org/ontology/bibo/DocumentStatus', u'http://purl.org/ontology/bibo/status/peerReviewed'))

                else:
                    item_type = item_dict['type']
                    if item_type.encode('utf-8') == 'Artículo':
                        print 'Articulo'
                        g.add((DOMINIO + u'resource/biblio/' + viaf_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/Article'))
                    elif item_type.encode('utf-8') == 'Sección de Libro':
                        print 'Seccion'
                        g.add((DOMINIO + u'resource/biblio/' + viaf_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/BookSection'))
                    elif item_type == u'Libro':
                        print 'Libro'
                        g.add((DOMINIO + u'resource/biblio/' + viaf_id, u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', u'http://purl.org/ontology/bibo/Book'))
                    elif item_type == u'PeerReviewed':
                        print 'Peer'
                        g.add((DOMINIO + u'resource/biblio/' + viaf_id, u'http://purl.org/ontology/bibo/DocumentStatus', u'http://purl.org/ontology/bibo/status/peerReviewed'))
                
if __name__ == "__main__":
    main()
        
