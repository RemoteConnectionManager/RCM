--[[

 Example lua script demonstrating the SLURM job_submit/lua interface.
 This is only an example, not meant for use in its current form.

 For use, this script should be copied into a file name "job_submit.lua"
 in the same directory as the SLURM configuration file, slurm.conf.

--]]

function os.capture(cmd, raw)
    local f = assert(io.popen(cmd, 'r'))
    local s = assert(f:read('*a'))
    f:close()
    if raw then return s end
    s = string.gsub(s, '^%s+', '')
    s = string.gsub(s, '%s+$', '')
    s = string.gsub(s, '[\n\r]+', ' ')
    return s
end

function split(str, pat)
   local t = {}  -- NOTE: use {n = 0} in Lua-5.0
   local fpat = "(.-)" .. pat
   local last_end = 1
   local s, e, cap = str:find(fpat, 1)
   while s do
      if s ~= 1 or cap ~= "" then
         table.insert(t,cap)
      end
      last_end = e+1
      s, e, cap = str:find(fpat, last_end)
   end
   if last_end <= #str then
      cap = str:sub(last_end)
      table.insert(t, cap)
   end
   return t
end

function check_billing(job_desc, avail_billing, partition)
    local max_int = 1000000000
    local def_wtime = 30
    local def_mem = {bdw="3000 * num_cpus", knl="86000", skl="182000"}
    local formula = {bdw="math.max(num_cpus * 0.25, mem * 0.072 / 1024)", 
                     knl="num_nodes * 272 * 0.03125", 
                     skl="num_nodes * 48 * 0.2"}
    local _, _, pname = string.find(partition, "^(%a%a%a)")
    if math.abs(job_desc.max_nodes) < max_int then
        max_nodes = job_desc.max_nodes
    else
        max_nodes = 0
    end
    if math.abs(job_desc.min_nodes) < max_int then
        min_nodes = job_desc.min_nodes
    else
        min_nodes = 1
    end
    num_nodes = math.max(max_nodes, min_nodes)
    num_cpus = job_desc.min_cpus
    if math.abs(job_desc.pn_min_memory) < max_int then
        mem = job_desc.pn_min_memory
    else
        local f = loadstring("return " .. def_mem[pname])
        mem = f()
    end
    if math.abs(job_desc.time_limit) < max_int then
        wtime = job_desc.time_limit
    else
        wtime = def_wtime
    end
    local f = loadstring("return wtime * " .. formula[pname])
    required_billing = math.ceil(f())
    --slurm.log_user("num_nodes %s, num_cpus %s, mem %s, wtime %s, required_billing %s, avail_billing %s", num_nodes, num_cpus, mem, wtime, required_billing, avail_billing)
    return (required_billing < avail_billing)
end

function load_billing(account)
    if not string.find(account, "_") then
        return nil
    end
    local output = os.capture("/usr/bin/sshare -nP --format=GrpTRESMins,GrpTRESRaw,TRESRunMins -lA " .. account)
    if output == "" then
        return nil
    end
    local t = split(output, "|cpu=%d+,mem=%d+,energy=%d+,node=%d+,")
    local billing = {}
    billing.GrpTRESMins, _ = string.gsub(t[1], "billing=", "")
    billing.GrpTRESRaw,  _ = string.gsub(t[2], "billing=", "")
    billing.TRESRunMins, _ = string.gsub(t[3], "billing=", "")
    --slurm.log_user("output: %s", output)
    --slurm.log_user("output: %s %s %s", t[1],t[2],t[3])
    --slurm.log_user("avail_billing: %s", billing.GrpTRESMins - billing.GrpTRESRaw - billing.TRESRunMins)
    return math.abs(billing.GrpTRESMins - billing.GrpTRESRaw - billing.TRESRunMins)
end

function get_partition(job_desc, part_list)
    local partition = job_desc.partition
    if not partition then
        for name, part in pairs(part_list) do
            if part.flag_default ~= 0 then
                partition = part.name
                slurm.log_user("no partition specified, using default partition %s", partition)
                break
            end
        end
    else
        local found = false
        for name, part in pairs(part_list) do
            if partition == part.name then
                found = true
                break
            end
        end
        if not found then
            slurm.log_user("invalid partition %s", partition)
            return nil
        end
    end
    return partition
end

function get_account(job_desc, partition)
    local account = job_desc.account
    if not account then
        account = job_desc.default_account
        slurm.log_user("no account specified, using your default account %s", account)
    else
        account = string.lower(account)
    end
    -- check EUROFUSION partitions access
    if string.find(account, "^fua") or string.find(account, "^fusio") then
        if not string.find(partition, "_fua_") then
            slurm.log_user("invalid partition %s for EUROFUSION account %s", partition, account)
            return nil
        end
    else
        if string.find(partition, "_fua_") then
            slurm.log_user("invalid partition %s for account %s", partition, account)
            return nil
        end
    end
    return account
end

function slurm_job_submit(job_desc, part_list, submit_uid)
    local account = job_desc.account
    local partition = job_desc.partition
    local qos = job_desc.qos or "normal"
    local jobname = job_desc.name
    local partnames = {bdw="marcon1", knl="marcon2", skl="marcon3"}
    local partition = get_partition(job_desc, part_list)
    if not partition then return slurm.ERROR end
    -- system
    if string.find(partition, "system") then
        if not job_desc.features then
            slurm.log_user("%s partition requires one of these features: bdw,knl,skl", partition)
            return slurm.ERROR
        elseif string.find(job_desc.features, "bdw") then
            job_desc.comment = "bdw"
        elseif string.find(job_desc.features, "knl") then
            job_desc.comment = "knl"
        elseif string.find(job_desc.features, "skl") then
            job_desc.comment = "skl"
        else
            slurm.log_user("%s partition requires one of these features: bdw,knl,skl", partition)
            return slurm.ERROR
        end
        return slurm.SUCCESS
    end
    -- serial
    if string.find(partition, "_all_") then
        return slurm.SUCCESS
    end
    -- RCM
    if string.find(qos, "%f[%w_%-]qos_rcm%f[^%w_%-]") then
        if not jobname or not string.find(jobname, "%-slurm%-") then
            slurm.log_user("invalid qos usage for %s", qos)
            return slurm.ERROR
        end
        return slurm.SUCCESS
    end
    -- EUROFUSION GATEWAY
    -- following line commented to enable bdw submission after budget migration until A1 decommission
    -- if string.find(partition, "fua_gw") or (string.find(qos, "qos_gw") and partition == "bdw_usr_prod") then
    if string.find(partition, "fua_gw") then
        return slurm.SUCCESS
    end
    if not account then
        account = job_desc.default_account
        slurm.log_user("no account specified, using your default account %s", account)
    else
        account = string.lower(account)
    end
    if string.find(partition, "skl_fua_new") and string.find(account, "cin_staff") then
        return slurm.SUCCESS
    end
    if string.find(account, "^fua") or string.find(account, "^fusio") then
        if not string.find(partition, "_fua_") then
            slurm.log_user("invalid partition %s for EUROFUSION account %s", partition, account)
            return slurm.ERROR
        end
    else
        if string.find(partition, "_fua_") then
            slurm.log_user("invalid partition %s for account %s", partition, account)
            return slurm.ERROR
        end
    end
--[[
    local account = get_account(job_desc, partition)
    if not account then return slurm.ERROR end
--]]
--[[
    local billing = load_billing(account)
    if not billing then
        slurm.log_user("invalid account %s", account)
        return slurm.ERROR
    elseif not check_billing(job_desc, billing, partition) then
        slurm.log_user("insufficient budget to run your job with account %s", account)
        return slurm.ERROR
    end
--]]
    local _, _, pname = string.find(partition, "^(%a%a%a)")
    local pattern = "%f[%w_%-]" .. string.gsub(account, "%-", "%%-") .. "%f[^%w_%-]"
-- AP mod 20180912 added if for accountattivi_marcon* files SDHPCSY-14128
    if string.find(qos, "lowprio") then
        filename="/cinecalocal/scripts/accountattivi_" .. partnames[pname]
    else
--        filename="yesbatch.new_" .. partnames[pname]
        filename="/cinecalocal/scripts/yesbatch.new_" .. partnames[pname]
    end
    local f = assert(io.open(filename, "r"))
    local account_list = string.lower(f:read("*all"))
    f:close()
    if not string.match(account_list, pattern) then
        slurm.log_user("invalid account or expired budget")
        return slurm.ERROR
    end
    return slurm.SUCCESS
end

function slurm_job_modify(job_desc, job_rec, part_list, modify_uid)
    return slurm.SUCCESS
end

slurm.log_info("initialized")
--return slurm.SUCCESS
