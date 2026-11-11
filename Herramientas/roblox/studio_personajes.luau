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
	if not t then t = workspace:FindFirstChild(nombre) end       -- objetos y escenarios (sin Humanoid): hacha, cueva...
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
				if c.Parent:IsA("Accoutrement") then       -- Accessory o Hat viejo (sale en el OBJ igual)
					local t = c.Parent:IsA("Accessory") and (tostring(c.Parent.AccessoryType):gsub("Enum.AccessoryType.", "")) or "Hat"
					table.insert(accs, {nombre = c.Parent.Name, accType = (t == "Unknown") and "Hat" or t,
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

-- _G.CL_r6a15(modeloR6, "Nombre_R15", plantillaR15, desplazamiento, tipos) -> copia R15 del personaje R6 (2026-11-10)
-- plantillaR15: cualquier personaje R15 de cuerpo blocky del lugar (MeshId 1699715xxx). Si es nil, se crea uno con
-- Players:CreateHumanoidModelFromDescription (2026-11-11). Pasa ropa clasica, colores, cara y accesorios (Hats viejos
-- y piezas sueltas como el pelo se vuelven Accessory soldados a la cabeza).
-- tipos: {NombreAccesorio = Enum.AccessoryType.Hair, ...}. Para piezas sueltas: tipos["<pieza>_nombre"] = "Pelo".
-- 2026-11-11 (EP012): la copia toma el TAMANO del R6 (ninos de torso 1.2), y las piezas dentro de Models (capa, mascara) tambien se vuelven Accessory: tipos["<Model>"] = AccessoryType
-- (Jacket = se deforma con el cuerpo, Back = pegada al torso, Face = a la cabeza).
-- OJO: Studio pinta la ropa clasica y la cara en la textura del cuerpo SOLO cuando la camara ve al personaje: antes de
-- exportar cada copia, apuntarle la camara (screen_capture con camera_position) y esperar ~3 s. Si no, sale sin ropa.
-- No toca el R6 original; la copia queda en el Workspace (borrarla al terminar de exportar).
local BODY6 = {Head=1, Torso=1, ["Left Arm"]=1, ["Right Arm"]=1, ["Left Leg"]=1, ["Right Leg"]=1, HumanoidRootPart=1}
local MAP6 = {Head={"Head"}, Torso={"UpperTorso","LowerTorso"}, ["Left Arm"]={"LeftUpperArm","LeftLowerArm","LeftHand"},
	["Right Arm"]={"RightUpperArm","RightLowerArm","RightHand"}, ["Left Leg"]={"LeftUpperLeg","LeftLowerLeg","LeftFoot"},
	["Right Leg"]={"RightUpperLeg","RightLowerLeg","RightFoot"}}
_G.CL_r6a15 = function(src, nombre, plantilla, offset, tipos)
	tipos = tipos or {}
	local m
	if plantilla then
		m = plantilla:Clone()
	else
		m = game:GetService("Players"):CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R15)
	end
	m.Name = nombre
	for _, c in ipairs(m:GetChildren()) do
		if c:IsA("Clothing") or c:IsA("Accoutrement") or c:IsA("BodyColors") or c:IsA("Configuration") or c:IsA("LuaSourceContainer")
			or c:IsA("Model") or c:IsA("ShirtGraphic") or c:IsA("CharacterMesh") then c:Destroy() end
	end
	for _, c in ipairs(src:GetChildren()) do
		if c:IsA("Clothing") or c:IsA("BodyColors") or c:IsA("ShirtGraphic") then c:Clone().Parent = m end
	end
	for p6, list in pairs(MAP6) do
		local sp = src:FindFirstChild(p6)
		if sp then for _, n in ipairs(list) do m[n].Color = sp.Color end end
	end
	local k = src.Torso.Size.Y / 2                         -- ninos: torso 1.2 -> la copia al 60 %
	if math.abs(k - 1) > 0.01 then m:ScaleTo(m:GetScale() * k) end
	local target = src.HumanoidRootPart.CFrame + (offset or Vector3.new(0, 0, 10))
	m:PivotTo(target * m.HumanoidRootPart.CFrame:Inverse() * m:GetPivot())
	-- cara: las calcomanias del R6 pasan a la cabeza R15 (Studio las pinta en la textura del cuerpo al exportar)
	for _, c in ipairs(m.Head:GetChildren()) do if c:IsA("Decal") then c:Destroy() end end
	for _, c in ipairs(src.Head:GetChildren()) do if c:IsA("Decal") then c:Clone().Parent = m.Head end end
	local srcHead, newHead = src.Head, m.Head
	local n = 0
	local function addAcc(handle, name, accType)
		local rel = srcHead.CFrame:ToObjectSpace(handle.CFrame)   -- misma posicion respecto a la cabeza
		local acc = Instance.new("Accessory"); acc.Name = name
		pcall(function() acc.AccessoryType = accType end)
		local h = handle:Clone(); h.Name = "Handle"
		for _, d in ipairs(h:GetDescendants()) do
			if d:IsA("JointInstance") or d:IsA("WeldConstraint") or d:IsA("Camera") then d:Destroy() end
		end
		h.Anchored = false
		h.CFrame = newHead.CFrame * rel
		-- pieza sin Attachment (capa, mascara de un Model): el Humanoid la acomodaria como sombrero ENCIMA de la cabeza.
		-- Se le pone un Attachment que coincide con uno de la cabeza para que se quede donde estaba (2026-11-11).
		if not h:FindFirstChildWhichIsA("Attachment") then
			local ref = newHead:FindFirstChild("FaceCenterAttachment") or newHead:FindFirstChildWhichIsA("Attachment")
			if ref then
				local a = Instance.new("Attachment"); a.Name = ref.Name
				a.CFrame = h.CFrame:ToObjectSpace(newHead.CFrame * ref.CFrame)
				a.Parent = h
			end
		end
		h.Parent = acc
		local w = Instance.new("Weld"); w.Name = "AccessoryWeld"; w.Part0 = newHead; w.Part1 = h; w.C0 = rel; w.Parent = h
		acc.Parent = m
		n += 1
	end
	for _, c in ipairs(src:GetChildren()) do
		if c:IsA("Accoutrement") then
			local h = c:FindFirstChild("Handle")
			if h then addAcc(h, c.Name, tipos[c.Name] or Enum.AccessoryType.Hat) end
		elseif c:IsA("Model") then                           -- capa, mascara: cada pieza visible es un accesorio
			for _, d in ipairs(c:GetDescendants()) do
				if d:IsA("BasePart") and d.Transparency < 1 then
					addAcc(d, (tipos[d.Name .. "_nombre"] or c.Name), tipos[d.Name] or tipos[c.Name] or Enum.AccessoryType.Hat)
				end
			end
		elseif c:IsA("BasePart") and not BODY6[c.Name] then
			addAcc(c, tipos[c.Name .. "_nombre"] or "Pelo", tipos[c.Name] or Enum.AccessoryType.Hair)
		end
	end
	m.Parent = workspace
	return nombre .. ": ok, accesorios=" .. n .. ", escala=" .. string.format("%.2f", k)
end

-- _G.CL_juntas(modelo) -> JSON del esqueleto de un modelo con articulaciones PROPIAS (no R15: ciervo, monstruos,
-- animales; 2026-11-11, EP012). Lo usa Herramientas/blender/rig_motor6d.py. Da cada pieza (CFrame, tamano, si se ve y
-- su lugar en el OBJ), cada Motor6D (Part0, Part1, C0, C1) y las soldaduras (Weld/WeldConstraint). No modifica nada.
local function cf12(cf)
	local t = {cf:GetComponents()}
	for i, v in ipairs(t) do t[i] = math.floor(v * 10000 + 0.5) / 10000 end
	return t
end
_G.CL_juntas = function(modelo)
	local piezas, motores, sold, k = {}, {}, {}, 0
	local d = modelo:GetDescendants()
	for i = #d, 1, -1 do                                   -- mismo orden que los grupos del OBJ
		local c = d[i]
		if c:IsA("BasePart") then
			local vis = c.Transparency < 1
			if vis then k += 1 end
			table.insert(piezas, {n = c.Name, cf = cf12(c.CFrame), s = {c.Size.X, c.Size.Y, c.Size.Z}, obj = vis and k or 0})
		elseif c:IsA("Motor6D") and c.Part0 and c.Part1 then
			table.insert(motores, {n = c.Name, p0 = c.Part0.Name, p1 = c.Part1.Name, c0 = cf12(c.C0), c1 = cf12(c.C1)})
		elseif (c:IsA("Weld") or c:IsA("WeldConstraint")) and c.Part0 and c.Part1 then
			table.insert(sold, {p0 = c.Part0.Name, p1 = c.Part1.Name})
		end
	end
	local raiz = modelo.PrimaryPart or modelo:FindFirstChild("HumanoidRootPart")
	return HS:JSONEncode({nombre = modelo.Name, raiz = raiz and raiz.Name or nil,
		mira = raiz and {raiz.CFrame.LookVector.X, raiz.CFrame.LookVector.Z} or nil,
		piezas = piezas, motores = motores, soldaduras = sold})
end

return "listo: _G.CL_isolate, _G.CL_restore, _G.CL_datos, _G.CL_r6a15, _G.CL_juntas"
