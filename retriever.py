import os,sys
from optparse import OptionParser
import util
import glob
import json
import datetime
import subprocess




###############################
def main():


    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-i","--infile",action="store",dest="infile",help="")
    parser.add_option("-o","--outfile",action="store",dest="outfile",help="")
    (options,args) = parser.parse_args()

    for key in ([ options.infile, options.outfile]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    record_type = "protein"
    in_file = options.infile
    out_file = options.outfile

    config_obj = json.load(open("conf/config.json"))
    fields_info = json.load(open("conf/fields.json"))
    main_id_field = config_obj["main_id_field"][record_type]

    rel = config_obj["release"]

    in_obj = json.load(open(in_file, "r"))
    



    db_dir = config_obj["data_dir"] + "/releases/data/%s/jsondb/%sdb/" % (rel, record_type)
    n1, n2 = 0, 0
    obj_list = []
    for input_id in in_obj["acclist"]:
        record_file = db_dir + input_id + ".json"
        doc = json.load(open(record_file)) if os.path.isfile(record_file) else{}
        n1 += 1 if doc != {} else 0
        n2 += 1 if doc == {} else 0
        ret_obj = util.get_record_obj(input_id, doc, record_type, main_id_field, fields_info)
        if ret_obj["error_list"] == []:
            obj_list.append(ret_obj["record_obj"])



    disease_db_dir = config_obj["data_dir"] + "/releases/data/%s/jsondb/diseasedb/" % (rel)
    disease_dict_file = "conf/disease-dict-%s.json" % (rel)
    if os.path.isfile(disease_dict_file) == False:
        util.dump_tree_db("disease", disease_db_dir, disease_dict_file)
    disease_dict = json.load(open(disease_dict_file))
    
    go_db_dir = config_obj["data_dir"] + "/releases/data/%s/jsondb/godb/" % (rel)
    go_dict_file = "conf/go-dict-%s.json" % (rel)
    if os.path.isfile(go_dict_file) == False:
        util.dump_tree_db("go", go_db_dir, go_dict_file)
    go_dict = json.load(open(go_dict_file))



    for obj in obj_list:
        for f in ["disease_protein", "disease_snv", "disease_expression", "go_mf","go_bp", "go_cc"]:
            seen = {}
            for o in obj[f]["value"]:
                o = json.loads(o)
                seen[o["id"]] = True
            obj[f]["lineage_down"] = []
            tmp_tree_dict = disease_dict if f.find("disease_") != -1 else go_dict
            for p_id in seen:
                p_name = tmp_tree_dict[p_id]["name"]
                for i in range(0, len(tmp_tree_dict[p_id]["id_list"])):
                    c_id = tmp_tree_dict[p_id]["id_list"][i]
                    c_name = tmp_tree_dict[c_id]["name"] if c_id in tmp_tree_dict else ""
                    if c_name == "" and "name_list" in tmp_tree_dict[p_id]:
                        c_name = tmp_tree_dict[p_id]["name_list"][i]
                    o = {"id":c_id, "name":c_name, "pid":p_id, "pname":p_name}
                    obj[f]["lineage_down"].append(json.dumps(o))


    f_obj_list = obj_list
    if "columns" in in_obj:
        if len(in_obj["columns"]) > 0:
            ret_obj = util.filter_obj_list(in_obj["columns"], obj_list)
            if ret_obj["error_list"] == []:
                f_obj_list = ret_obj["f_obj_list"]
            else:
                util.write_output(ret_obj, out_file)
                exit()


    col_dict = {"input_id":"Input ID", "record_id":"Record ID"}
    for obj in in_obj["columns"]:
        col_id = obj["column_id"]
        fil = obj["filter"] if "filter" in obj else obj["label"]
        col_dict[col_id] = fil

    query_obj = {
        "jobtype": "batch_retrieval",
        "parameters": in_obj
    }
    out_doc = {"columns":col_dict, "rows":f_obj_list, "query":query_obj}
    util.write_output(out_doc, out_file)


    return



if __name__ == '__main__':
    main()

