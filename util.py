import os
import string
import json
import random
from collections import OrderedDict
import gzip
import csv
import datetime
import pytz
import hashlib
import glob
import subprocess

def format_obj_value(obj, o_type):

    output = "%s (%s)" % (obj["name"], obj["id"])
    if o_type == "id":
        output = obj["id"]
    elif o_type == "name":
        output = obj["name"]

    return output




def get_record_obj(input_id, doc, record_type, main_id_field, fields_info):


    error_list = []

    record_obj = {
        "input_id":{"value":input_id, "type":"str"}, 
        "record_id_field":{"value":main_id_field, "type":"str"}
    }
    for f in fields_info[record_type]:
        record_obj[f] = ""

    if doc == {}:
        return record_obj



    #print (json.dumps(doc, indent=4))
    #exit()

    record_id = doc[main_id_field] if main_id_field in doc else ""
    record_obj["record_id"] = {"value":record_id, "type":"str"}

    if record_type == "protein":
        
        #-->species
        tax_id, tax_name = doc["species"][0]["taxid"], doc["species"][0]["name"]
        record_obj["species"] = {"value":{"id":tax_id, "name":tax_name}, "type":"obj"}

        #-->pdb_id
        sec = "structures"
        if sec in doc:
            seen = {}
            for obj in doc[sec]:
                if obj["type"] != "experimental":
                    continue
                seen[obj["pdb_id"]] = True
            record_obj["pdb_id"] = {"value":list(seen.keys()), "type":"list"}

        #-->gene_locus
        sec = "gene"
        if sec in doc:
            seen = {}
            for obj in doc[sec]:
                if obj["locus"] == {}:
                    continue
                chr_id, strand = obj["locus"]["chromosome"], obj["locus"]["strand"]
                s, e = obj["locus"]["start_pos"], obj["locus"]["end_pos"]
                val = "Chromosome: %s [%s-%s] (%sstrand)" % (chr_id,s, e, strand)
                seen[val] = True
            record_obj["gene_locus"] = {"value":list(seen.keys()), "type":"list"}

        #-->protein_locus
        sec = "isoforms"
        if sec in doc:
            seen = {}
            for obj in doc[sec]:
                if obj["isoform_ac"] == record_obj["record_id"]:
                    if obj["locus"] == {}:
                        continue
                    chr_id, strand = obj["locus"]["chromosome"], obj["locus"]["strand"]
                    s, e = obj["locus"]["start_pos"], obj["locus"]["end_pos"]
                    val = "Chromosome: %s [%s-%s] (%sstrand)" % (chr_id,s, e, strand)
                    seen[val] = True
            record_obj["protein_locus"] = {"value":list(seen.keys()), "type":"list"}
   
             
        #-->pathways
        sec = "pathway"
        if sec in doc:
            seen = {}
            for obj in doc[sec]:        
                name = obj["name"] 
                if obj["name"].strip() == "" and "description" in obj:
                    name = obj["description"]
                if name == "" or obj["id"].strip() == "":
                    continue
                val = json.dumps({"id":obj["id"], "name":name})
                seen[val] = True
            record_obj["pathways"] = {"value":list(seen.keys()), "type":"objlist"}


        #-->go_mf, go_bp, go_cc
        sec = "go_annotation"
        if sec in doc:
            cat_list = ["Molecular Function", "Biological Process", "Cellular Component"]
            seen = {cat_list[0]:{}, cat_list[1]:{}, cat_list[2]:{}}
            for obj in doc[sec]["categories"]:
                cat = obj["name"]
                if cat not in seen:
                    continue
                for o in obj["go_terms"]:
                    #val = "%s (%s)" % (o["name"], o["id"])
                    val = json.dumps({"id":o["id"], "name":o["name"]})
                    seen[cat][val] = True
            record_obj["go_mf"] = {"value":list(seen[cat_list[0]].keys()), "type":"objlist"}
            record_obj["go_bp"] = {"value":list(seen[cat_list[1]].keys()), "type":"objlist"}
            record_obj["go_cc"] = {"value":list(seen[cat_list[2]].keys()), "type":"objlist"}
            
        #-->diease_protein
        sec = "disease"
        if sec in doc:
            seen = {}
            for obj in doc[sec]:
                o = obj["recommended_name"]
                #val = "%s (%s)" % (o["name"], o["id"])
                val = json.dumps({"id":o["id"], "name":o["name"]})
                seen[val] = True
            record_obj["disease_protein"] = {"value":list(seen.keys()), "type":"objlist"}               


        #-->disease_snv
        sec = "snv"
        if sec in doc:
            seen = {}
            for obj in doc[sec]:
                if "disease" not in obj:
                    continue
                for o in obj["disease"]:
                    d_name, d_id = o["recommended_name"]["name"], o["recommended_name"]["id"]
                    #val = "%s (%s)" % (d_id, d_name)
                    val = json.dumps({"id":d_id, "name":d_name})
                    seen[val] = True
            record_obj["disease_snv"] = {"value":list(seen.keys()), "type":"objlist"}


        #-->disease_expression
        sec = "expression_disease"
        if sec in doc:
            seen = {}
            for obj in doc[sec]:
                if "disease" not in obj:
                    continue
                for o in obj["disease"]:
                    d_name, d_id = o["recommended_name"]["name"], o["recommended_name"]["id"]
                    #val = "%s (%s)" % (d_id, d_name)
                    val = json.dumps({"id":d_id, "name":d_name}) 
                    seen[val] = True
            record_obj["disease_expression"] = {"value":list(seen.keys()), "type":"objlist"}

    
        #-->is_biomarker
        sec = "biomarkers"
        record_obj["is_biomarker"] = {"value":False, "type":"boolean"}
        if sec in doc:
            if len(doc[sec]) > 0:
                record_obj["is_biomarker"] = {"value":True, "type":"boolean"}

        #-->n_glycosites_confirmed, n_glycosites_predicted, o_glycosites_confirmed, o_glycosites_predicted
        #-->glycosite_count_confirmed, glycosite_count
        sec = "glycosylation"
        if sec in doc:
            seen = {"nsites_confirmed":{}, "osites_confirmed":{}, "nsites_predicted":{}, "osites_predicted":{}}
            for obj in doc[sec]:
                if "start_pos" not in obj or "end_pos" not in obj:
                    continue
                if obj["start_pos"] < 0 or obj["end_pos"] < 0:
                    continue
                site = "%s-%s" % (obj["start_pos"], obj["end_pos"]) 

                site_cat_list = []
                if obj["site_category"] in ["reported", "reported_with_glycan", "automatic_literature_mining"]:
                    site_cat_list.append("confirmed")
                if obj["site_category"] in ["predicted", "predicted_with_glycan"]:
                    site_cat_list.append("predicted")
                
                if obj["type"] == "N-linked" and "confirmed" in site_cat_list:
                    seen["nsites_confirmed"][site] = True
                if obj["type"] == "O-linked" and "confirmed" in site_cat_list:
                    seen["osites_confirmed"][site] = True
                if obj["type"] == "N-linked" and "predicted" in site_cat_list:
                    seen["nsites_predicted"][site] = True
                if obj["type"] == "O-linked" and "predicted" in site_cat_list:
                    seen["osites_predicted"][site] = True

            l_11, l_12 = list(seen["nsites_confirmed"].keys()), list(seen["osites_confirmed"].keys())
            l_21, l_22 = list(seen["nsites_predicted"].keys()), list(seen["osites_predicted"].keys())
            record_obj["n_glycosites_confirmed"] = {"value":l_11, "type":"list"}
            record_obj["o_glycosites_confirmed"] = {"value":l_12, "type":"list"}
            record_obj["n_glycosites_predicted"] = {"value":l_21, "type":"list"}
            record_obj["o_glycosites_predicted"] = {"value":l_22, "type":"list"}
           
            nsites_confirmed = list(seen["nsites_confirmed"].keys()) 
            osites_confirmed = list(seen["osites_confirmed"].keys())
            nsites_predicted = list(seen["nsites_predicted"].keys())
            osites_predicted = list(seen["osites_predicted"].keys())

            set_confirmed = set(nsites_confirmed + osites_confirmed)
            set_all = set(nsites_confirmed + osites_confirmed + nsites_predicted + osites_predicted)
            record_obj["glycosite_count_confirmed"] = {"value":len(set_confirmed), "type":"int"}
            record_obj["glycosite_count"] = {"value":len(set_all), "type":"int"}


        #-->phosphosite_count
        sec = "phosphorylation"
        if sec in doc:
            seen = {}
            for obj in doc[sec]:
                if "start_pos" not in obj or "end_pos" not in obj:
                    continue
                if obj["start_pos"] < 0 or obj["end_pos"] < 0:
                    continue
                site = "%s-%s" % (obj["start_pos"], obj["end_pos"])
                seen[site] = True
            record_obj["phosphosite_count"] = {"value":len(list(seen.keys())), "type":"int"}


    return {"error_list":error_list, "record_obj":record_obj}



def get_match_value(record_id, val, f_val, v_type, f_type):

    new_val = ""
    if v_type == "str":
        if str(val).lower() == str(f_val).lower():
            new_val = val
    elif v_type == "list":
        for v in val:
            if str(v).lower() == str(f_val).lower():
                new_val = v
    elif v_type == "obj":
        val = json.loads(val)
        for k in val:
            if str(val[k]).lower() == str(f_val).lower():
                new_val = val
    elif v_type == "objlist":
        for o in val:
            o = json.loads(o)
            for k in o:
                if str(o[k]).lower() == str(f_val).lower():
                    oo = o
                    if f_type == "hierarchy":
                        oo = {"id":o["pid"], "name":o["pname"]}
                        #if f_val == "growth factor activity":
                        #    print (record_id, o, oo)
                    if new_val == "":
                        new_val = {}
                    new_val[oo["id"]] = json.dumps(oo)

    tmp_list = []
    if v_type == "objlist":
        for id_val in new_val:
            tmp_list.append(new_val[id_val])
        new_val = tmp_list

    return new_val


def filter_obj_list(filter_obj_list, obj_list):


    error_list = []
    f_obj_list = []

    seen_field = {}
    for obj in filter_obj_list:
        f = obj["id"]
        if f not in obj_list[0]:
            error_list.append("invalid field=%s" % (f))
        else:
            if f not in seen_field:
                seen_field[f] = []
            seen_field[f].append(obj)

    
    if error_list == []:
        #new_field_dict = {}
        #for f in seen_field:
        #    for i in range(0, len(seen_field[f])):
        #        new_f = "%s_%s" % (f, i + 1)
        #        new_field_dict[new_f] = f
        for obj in obj_list:
            record_id = obj["record_id"]["value"]
            new_obj = {}
            for f in ["input_id", "record_id"]:
                new_obj[f] = obj[f]["value"]
            for f in seen_field:
                for i in range(0, len(seen_field[f])):
                    new_f = "%s_%s" % (f, i + 1) 
                    oo = seen_field[f][i] 
                    oo["column_id"] = new_f
                    o_type = oo["output_type"] if "output_type" in oo else ""
                    f_type = oo["filter_type"] if "filter_type" in oo else ""
                    f_val = oo["filter"] if "filter" in oo else ""
                    val, v_type = obj[f]["value"], obj[f]["type"]
                    new_val = ""
                    if f_type == "none":
                        new_val = val
                    elif f_type == "exact":
                        new_val = get_match_value(record_id,val, f_val, v_type, f_type)
                    elif f_type == "hierarchy":
                        val = obj[f]["lineage_down"]
                        new_val = get_match_value(record_id, val, f_val, v_type, f_type)
                    if new_val != "":
                        if v_type == "str":
                            new_val = new_val
                        elif v_type == "list":
                            new_val = ";".join(new_val)
                        elif v_type == "obj":
                            new_val = format_obj_value(new_val, o_type)
                        elif v_type == "objlist":
                            l = []
                            for o in new_val:
                                o = json.loads(o)
                                output = format_obj_value(o, o_type)
                                l.append(output)
                            new_val = ";".join(l)
                    new_obj[new_f] = new_val 
            f_obj_list.append(new_obj)


    return {"error_list":error_list, "f_obj_list":f_obj_list}





def dump_tree_db(tree_type, db_dir, out_file):

    tmp_dict = {}
    file_list = glob.glob(db_dir + "*.json")
    for in_file in file_list:
        doc = json.load(open(in_file))
        d_id, d_name = "", ""
        if tree_type == "disease":
            d_id, d_name = doc["recommended_name"]["id"], doc["recommended_name"]["name"]
        if tree_type == "go":
            d_id, d_name = doc["goid"], doc["name"]
        tmp_dict[d_id] = {"name":d_name, "id_list":doc["id_list"]}
        if "name_list" in doc:
             tmp_dict[d_id]["name_list"] = doc["name_list"]

    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(tmp_dict)))
    return 

   


def write_output(out_doc, out_file):

    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(out_doc, indent=4)))

    cmd = "chmod 775 %s" % (out_file)
    x = subprocess.getoutput(cmd)
 
    return


