#include "domain/SaveCodec.h"
#include <bit>
#include <limits>

namespace domain {
namespace {
constexpr std::array<std::uint8_t,8> Magic={'S','H','O','E','N','M','1',0};
constexpr std::size_t HeaderSize=28;
std::uint64_t Checksum(std::span<const std::uint8_t> bytes) {
    std::uint64_t hash=14695981039346656037ULL;
    for(auto b:bytes) {hash^=b; hash*=1099511628211ULL;}
    return hash;
}
struct Writer {
    std::vector<std::uint8_t> bytes;
    void U8(std::uint8_t n) {bytes.push_back(n);}
    void U32(std::uint32_t n) {for(int i=0;i<4;++i) U8(static_cast<std::uint8_t>(n>>(8*i)));}
    void U64(std::uint64_t n) {for(int i=0;i<8;++i) U8(static_cast<std::uint8_t>(n>>(8*i)));}
    void I64(std::int64_t n) {U64(std::bit_cast<std::uint64_t>(n));}
    void Double(double n) {U64(std::bit_cast<std::uint64_t>(n));}
    void String(const std::string& s) {U32(static_cast<std::uint32_t>(s.size())); bytes.insert(bytes.end(),s.begin(),s.end());}
    template<class Container> void Count(const Container& c) {U32(static_cast<std::uint32_t>(c.size()));}
};
struct Reader {
    std::span<const std::uint8_t> bytes; std::size_t pos=0; std::string error;
    void Fail(const char* message) {if(error.empty()) error=message;}
    std::uint8_t U8() {if(pos>=bytes.size()) {Fail("Snapshot is truncated."); return 0;} return bytes[pos++];}
    std::uint32_t U32() {std::uint32_t n=0; for(int i=0;i<4;++i) n|=static_cast<std::uint32_t>(U8())<<(8*i); return n;}
    std::uint64_t U64() {std::uint64_t n=0; for(int i=0;i<8;++i) n|=static_cast<std::uint64_t>(U8())<<(8*i); return n;}
    std::int64_t I64() {return std::bit_cast<std::int64_t>(U64());}
    double Double() {return std::bit_cast<double>(U64());}
    bool Bool() {auto b=U8(); if(b>1) Fail("Snapshot boolean is invalid."); return b==1;}
    std::uint32_t Count() {auto n=U32(); if(n>MaxServiceRecords || !error.empty()) {Fail("Snapshot record count exceeds the foundation limit."); return 0;} return n;}
    std::string String() {
        auto n=U32(); if(n>256 || n>bytes.size()-pos || !error.empty()) {Fail("Snapshot string exceeds its bounds."); return {};}
        std::string value(reinterpret_cast<const char*>(bytes.data()+pos),n); pos+=n; return value;
    }
    template<class Map,class Value> void Insert(Map& map, Value&& value) {
        auto id=value.id; if(!map.emplace(id,std::move(value)).second) Fail("Snapshot has duplicate record IDs.");
    }
};
void EncodeWorld(Writer& p,const World& w) {
    p.I64(w.campaign_day); p.U32(static_cast<std::uint32_t>(w.speed)); p.I64(w.subday_microseconds); p.I64(w.formation_substep_microseconds);
    p.U64(w.revision); p.U64(w.next_id); p.U64(w.next_transaction_id);
    p.I64(w.initial_population); p.I64(w.births); p.I64(w.admitted_immigrants); p.I64(w.recorded_emigrants);
    for(const auto& r:w.rng) {p.U64(r.state); p.U64(r.counter);}
    p.Count(w.applied_transaction_ids); for(auto id:w.applied_transaction_ids) p.U64(id);
    p.Count(w.settlements);
    for(const auto& [id,s]:w.settlements) {
        p.U64(id); p.String(s.name);
        const auto& r=s.resources; p.I64(r.food); p.I64(r.timber); p.I64(r.iron); p.I64(r.treasury); p.I64(r.seed_grain); p.I64(r.fuel); p.I64(r.equipment);
    }
    p.Count(w.districts); for(const auto& [id,d]:w.districts) {p.U64(id); p.U64(d.settlement_id); p.String(d.name);}
    p.Count(w.cohorts);
    for(const auto& [id,c]:w.cohorts) {
        p.U64(id); p.U64(c.settlement_id); p.U64(c.district_id); p.U8(static_cast<std::uint8_t>(c.occupation)); p.U8(static_cast<std::uint8_t>(c.skill)); p.U8(static_cast<std::uint8_t>(c.estate));
        p.I64(c.available); p.I64(c.dependent_or_ineligible); p.I64(c.recovering_home);
    }
    p.Count(w.services);
    for(const auto& [id,s]:w.services) {
        p.U64(id); const auto& o=s.origin; p.U64(o.settlement_id); p.U64(o.district_id); p.U64(o.cohort_id);
        p.U8(static_cast<std::uint8_t>(o.occupation)); p.U8(static_cast<std::uint8_t>(o.skill)); p.U8(static_cast<std::uint8_t>(o.estate)); p.U8(static_cast<std::uint8_t>(s.status)); p.U64(s.formation_id);
    }
    p.Count(w.formations);
    for(const auto& [id,f]:w.formations) {
        p.U64(id); p.String(f.name); p.Count(f.service_ids); for(auto sid:f.service_ids) p.U64(sid);
        p.Double(f.x); p.Double(f.y); p.Double(f.facing); p.Double(f.target_x); p.Double(f.target_y); p.Double(f.target_facing);
        p.U8(f.moving); p.U8(f.control_group); p.U8(f.demobilized); p.U8(static_cast<std::uint8_t>(f.role));
    }
    p.Count(w.generals);
    for(const auto& [id,g]:w.generals) {
        p.U64(id); p.String(g.name);
        for(int a:{g.command,g.coordination,g.scouting,g.secrecy,g.terrain_knowledge,g.logistics}) p.U32(static_cast<std::uint32_t>(a));
    }
}
World ReadWorld(Reader& p) {
    World w;
    w.campaign_day=p.I64(); auto speed=p.U32(); if(speed>10) p.Fail("Snapshot speed is invalid."); w.speed=static_cast<int>(speed);
    w.subday_microseconds=p.I64(); w.formation_substep_microseconds=p.I64(); w.revision=p.U64(); w.next_id=p.U64(); w.next_transaction_id=p.U64();
    w.initial_population=p.I64(); w.births=p.I64(); w.admitted_immigrants=p.I64(); w.recorded_emigrants=p.I64();
    for(auto& r:w.rng) {r.state=p.U64(); r.counter=p.U64();}
    auto n=p.Count(); for(std::uint32_t i=0;i<n && p.error.empty();++i) if(!w.applied_transaction_ids.insert(p.U64()).second) p.Fail("Duplicate applied transaction ID.");
    n=p.Count();
    for(std::uint32_t i=0;i<n && p.error.empty();++i) {
        Settlement s; s.id=p.U64(); s.name=p.String(); auto& r=s.resources;
        r.food=p.I64(); r.timber=p.I64(); r.iron=p.I64(); r.treasury=p.I64(); r.seed_grain=p.I64(); r.fuel=p.I64(); r.equipment=p.I64(); p.Insert(w.settlements,std::move(s));
    }
    n=p.Count(); for(std::uint32_t i=0;i<n && p.error.empty();++i) {District d; d.id=p.U64(); d.settlement_id=p.U64(); d.name=p.String(); p.Insert(w.districts,std::move(d));}
    n=p.Count();
    for(std::uint32_t i=0;i<n && p.error.empty();++i) {
        Cohort c; c.id=p.U64(); c.settlement_id=p.U64(); c.district_id=p.U64(); c.occupation=static_cast<Occupation>(p.U8()); c.skill=static_cast<Skill>(p.U8()); c.estate=static_cast<Estate>(p.U8());
        c.available=p.I64(); c.dependent_or_ineligible=p.I64(); c.recovering_home=p.I64(); p.Insert(w.cohorts,std::move(c));
    }
    n=p.Count();
    for(std::uint32_t i=0;i<n && p.error.empty();++i) {
        ServiceRecord s; s.id=p.U64(); auto& o=s.origin; o.settlement_id=p.U64(); o.district_id=p.U64(); o.cohort_id=p.U64();
        o.occupation=static_cast<Occupation>(p.U8()); o.skill=static_cast<Skill>(p.U8()); o.estate=static_cast<Estate>(p.U8()); s.status=static_cast<ServiceStatus>(p.U8()); s.formation_id=p.U64(); p.Insert(w.services,std::move(s));
    }
    n=p.Count(); std::size_t total_members=0;
    for(std::uint32_t i=0;i<n && p.error.empty();++i) {
        Formation f; f.id=p.U64(); f.name=p.String(); auto count=p.Count(); total_members+=count;
        if(total_members>MaxServiceRecords) {p.Fail("Snapshot total formation membership exceeds the limit."); break;}
        for(std::uint32_t j=0;j<count && p.error.empty();++j) f.service_ids.push_back(p.U64());
        f.x=p.Double(); f.y=p.Double(); f.facing=p.Double(); f.target_x=p.Double(); f.target_y=p.Double(); f.target_facing=p.Double();
        f.moving=p.Bool(); f.control_group=p.U8(); f.demobilized=p.Bool(); f.role=static_cast<TroopRole>(p.U8()); p.Insert(w.formations,std::move(f));
    }
    n=p.Count();
    for(std::uint32_t i=0;i<n && p.error.empty();++i) {
        General g; g.id=p.U64(); g.name=p.String();
        for(int* a:{&g.command,&g.coordination,&g.scouting,&g.secrecy,&g.terrain_knowledge,&g.logistics}) {auto value=p.U32(); if(value>100) p.Fail("Snapshot general attribute is invalid."); *a=static_cast<int>(value);}
        p.Insert(w.generals,std::move(g));
    }
    return w;
}
}
std::vector<std::uint8_t> EncodeSnapshot(const World& w) {
    if(!ValidateWorld(w).ok) return {};
    Writer p; EncodeWorld(p,w); if(p.bytes.size()>MaxSnapshotBytes-HeaderSize) return {};
    Writer out; for(auto b:Magic) out.U8(b); out.U32(SnapshotVersion); out.U64(p.bytes.size()); out.U64(Checksum(p.bytes));
    out.bytes.insert(out.bytes.end(),p.bytes.begin(),p.bytes.end()); return out.bytes;
}
DecodeResult DecodeSnapshot(std::span<const std::uint8_t> bytes) {
    if(bytes.size()<HeaderSize || bytes.size()>MaxSnapshotBytes) return {false,"Snapshot size is outside supported bounds.",{}};
    Reader h{bytes,0,{}};
    for(auto b:Magic) if(h.U8()!=b) return {false,"This is not a SHŌEN foundation snapshot.",{}};
    if(h.U32()!=SnapshotVersion) return {false,"Unsupported snapshot version; no migration is available.",{}};
    auto length=h.U64(); auto expected=h.U64();
    if(length!=bytes.size()-HeaderSize) return {false,"Snapshot length does not match its header.",{}};
    auto payload=bytes.subspan(HeaderSize);
    if(Checksum(payload)!=expected) return {false,"Snapshot checksum mismatch.",{}};
    Reader p{payload,0,{}}; auto w=ReadWorld(p);
    if(!p.error.empty()) return {false,p.error,{}};
    if(p.pos!=payload.size()) return {false,"Snapshot contains trailing payload data.",{}};
    auto validation=ValidateWorld(w); if(!validation.ok) return {false,validation.error,{}};
    return {true,{},std::move(w)};
}
Result LoadSnapshot(World& live,std::span<const std::uint8_t> bytes) {
    auto decoded=DecodeSnapshot(bytes); if(!decoded.ok) return {false,decoded.error,0};
    live=std::move(decoded.world); return {true,{},0};
}
}
