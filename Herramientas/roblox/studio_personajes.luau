-- Funciones para exportar personajes de Roblox Studio uno por uno (correr con execute_luau del MCP de Studio).
-- Pega este archivo una vez; despues:
--   _G.CL_isolate("NombreDelModelo")  -> deja SOLO ese personaje en el Workspace (lo demas va a ServerStorage)
--   (exportar con exportar_obj.ps1)
--   _G.CL_restore()                   -> regresa todo a su lugar (llamarlo SIEMPRE al terminar)
--   _G.CL_datos()                     -> JSON con la posicion de cada pieza y los accesorios en el orden del OBJ
--                                        (lo usa partes_json.py para nombrar bien las piezas)
-- Es reversible: solo cambia el Parent de las cosas; no borra ni guarda el lugar.
local SS = game:GetService("ServerStorage")
local HS = game:GetService("HttpService")
local TEMP = "_TEMP_EXPORT_CLAUDE"
local R15 = {Head=1,UpperTorso=1,LowerTorso=1,RightUpperArm=1,RightLowerArm=1,RightHand=1,LeftUpperArm=1,LeftLowerArm=1,
	LeftHand=1,RightUpperLeg=1,RightLowerLeg=1,RightFoot=1,LeftUpperLeg=1,LeftLowerLeg=1,LeftFoot=1}

local function personajes()
	local t = {}
	for _, d in ipairs(workspace:GetDescendants()) do
		if d:IsA("Humanoid") and d.Parent:IsA("Model") then table.insert(t, d.Parent) end
	end
	return t
end

_G.CL_restore = function()
	local h = SS:FindFirstChild(TEMP)
	if h then
		for _, c in ipairs(h:GetChildren()) do c.Parent = workspace end
		h:Destroy()
	end
	for _, c in ipairs(workspace:GetChildren()) do
		local orig = c:GetAttribute("_origParent")
		if orig then
			c:SetAttribute("_origParent", nil)
			local p = workspace:FindFirstChild(orig, true)
			if p then c.Parent = p end
		end
	end
	return "restaurado: " .. #workspace:GetChildren() .. " hijos en Workspace"
end

_G.CL_isolate = function(nombre)
	_G.CL_restore()
	local t
	for _, m in ipairs(personajes()) do if m.Name == nombre then t = m break end end
	if not t then return "NO ENCONTRADO " .. nombre end
	if t.Parent ~= workspace then t:SetAttribute("_origParent", t.Parent.Name); t.Parent = workspace end
	local h = Instance.new("Folder"); h.Name = TEMP; h.Parent = SS
	for _, c in ipairs(workspace:GetChildren()) do
		if c ~= t and not c:IsA("Camera") and not c:IsA("Terrain") then c.Parent = h end
	end
	game:GetService("Selection"):Set({t})
	return "aislado " .. t.Name
end

_G.CL_datos = function()
	local res = {}
	for _, m in ipairs(personajes()) do
		local cuerpo, accs = {}, {}
		local d = m:GetDescendants()
		for i = #d, 1, -1 do                       -- el OBJ sale en orden inverso de GetDescendants
			local c = d[i]
			if c:IsA("BasePart") and c.Name ~= "HumanoidRootPart" and c.Transparency < 1 then
				if c.Parent:IsA("Accessory") then
					table.insert(accs, {nombre = c.Parent.Name,
						accType = (tostring(c.Parent.AccessoryType):gsub("Enum.AccessoryType.", "")),
						wrap = c:FindFirstChildOfClass("WrapLayer") ~= nil})
				elseif R15[c.Name] and c.Parent == m then
					cuerpo[c.Name] = {c.Position.X, c.Position.Y, c.Position.Z}
				end
			end
		end
		local mira = m:FindFirstChild("HumanoidRootPart")
		res[m.Name] = {cuerpo = cuerpo, accs = accs, mira = mira and {mira.CFrame.LookVector.X, mira.CFrame.LookVector.Z} or nil}
	end
	return HS:JSONEncode(res)
end

return "listo: _G.CL_isolate, _G.CL_restore, _G.CL_datos"
